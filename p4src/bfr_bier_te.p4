#include "includes/bier_te/headers.p4"
#include "includes/bier_te/parser.p4"
#include "includes/bier_te/ip_forwarding.p4"
#include "includes/bier_te/classic_mc.p4"

metadata routing_metadata_t routing_metadata;
metadata bier_metadata_t bier_metadata;
metadata intrinsic_metadata_t intrinsic_metadata;
metadata bier_frr_metadata_t bier_frr_metadata;

control ingress {
    //apply(print_ingress_start);
    if(ethernet.etherType == 0xBBBB) {
        /* BIER-TE Paket empfangen */
        /* Filtern der Bits of Interes, Bit Mask steht in Metadaten */

        /* nur falls Paket frisch, nicht wenn es mitten in der Verarbeitung ist */
        if(bier_metadata.bits_of_interest == 0) {
            apply(get_bits_of_interest);
        }

        apply(frr_indication);
        
        apply(find_bit_pos) {
            hit {
                if(bier_metadata.bit_pos == bier_frr_metadata.bp) {
                    //aktuelle stelle ist vom Fehler betroffen
                    if(bier_frr_metadata.BitString == 0) {
                        apply(frr_copy_bitstring);
                    }               
                    apply(btaft);
                }
                else
                {
                    //aktuelle stelle ist nicht betroffen
                    apply(bift) {
                        local_decap {
                            if(valid(bier[1])) {
                                if(bier_frr_metadata.decap_done == 0) {
                                    apply(do_reinsert_encapsulated);
                                }
                            }
                            else {
                                apply(do_handover_mc_overlay);
                            }
                        }
                    }
                }
            }
        }
    }
    else if(ethernet.etherType == 0x0800)
    {
        /*
        Kein Hinzufügen eines Headers, sollte das Paket ein decap sein
        */
        if(bier_metadata.decap == 0) {
            /*
            Prüfen, ob BIER Header hinzugefügt werden soll
            */
            apply(bier_ingress);
        }

        /*
        Falls kein BIER Header hinzugefügt wurde, handelt es sich um
        normalen IPv4 Verkehr, entsprechend Forwarding anwenden
        */
        if(not valid(bier))
        {
            apply(ipv4_lpm);
            apply(forward);
        }
    }
    //apply(print_ingress_end);
}

control egress {
    //apply(print_egress_start);
    if(standard_metadata.instance_type == 2) {
        /*
        Falls ein egress Klon aus einem decap erzeugt wurde, dann wurde
        diesem Paket der Header entfernt und er muss neu angefügt werden
        */
        if(bier_metadata.decap == 1) {
            apply(do_restore_bier_table);
        }

        /*
        wORKAROUND: clone_egress_to_ingress gibt es in bmv2 nicht.
        Daher clone_e2e mit anschließender recirculation
        */
        if(bier_metadata.needs_cloning == 1) {
            apply(do_clone_recirculation_table);
        }
        //Gleicher Workaround fuer mehrmaligen Match auf BTAFT
        if(bier_frr_metadata.needs_recursion == 1 or 
            bier_frr_metadata.needs_cloning == 1) {
            apply(do_frr_recursion);
        }
    } else if(bier_metadata.needs_cloning == 1 
    or bier_metadata.decap == 1 
    or bier_frr_metadata.needs_recursion == 1 
    or bier_frr_metadata.needs_cloning == 1) {
        apply(do_cloning_table);
    }

    /*
    PKT_INSTANCE_TYPE_EGRESS_CLONE - 2
    PKT_INSTANCE_TYPE_RECIRC - 4
    PKT_INSTANCE_TYPE_RESUBMIT - 6
    */
    if (ethernet.etherType == 0x0800) {
        apply(send_frame);
    }
    if(bier_metadata.decap == 1) {
        if(valid(bier[1])) {
            //BIER in BIER Paket
            apply(do_remove_outer_bier_header);
        }
        else {
            apply(do_decap_table);
        }
    }
    //apply(print_egress_end);
}


action reinsert_encapsulated() {
    modify_field(bier_frr_metadata.decap_done, 1);
    resubmit(bier_FL);
}
table do_reinsert_encapsulated {
    actions {
        reinsert_encapsulated;
    }
}

action save_bp(bp) {
    modify_field(bier_frr_metadata.bp, bp);
    //check if this position affects the flow
    modify_field(bier_frr_metadata.flow_affected, bier_metadata.BitString_of_interest & (1 << (bp - 1)));
}

table frr_indication {
    reads {
        //Eintrag mit 0/0 lpm um hit zu erzeugen, sobald Eintrag vorhaden
        bier_frr_metadata.BitString: lpm;
    }
    actions {
        save_bp;
    }
}

action a_r_bm_apply() {
    //apply reset on inner BIER Header
    modify_field(bier.BitString, bier.BitString & ~bier_frr_metadata.reset_bm);
    
    //copy the old header to inner header
    copy_header(bier[1], bier[0]);

    //add new header on top
    add_header(bier[0]);
    //set next proto field
    modify_field(bier[0].Proto, BIER_PROTO_BIER); 

    //apply add on outer BIER Header
    modify_field(bier[0].BitString, bier_frr_metadata.add_bm);
    
    //no more recursion
    modify_field(bier_frr_metadata.needs_recursion, 0);

    //but a cloning to recirculate
    modify_field(bier_frr_metadata.needs_cloning, 1);

    //we must reset the boi to recalculate them in the next recirculation
    modify_field(bier_metadata.bits_of_interest, 0);
}

action a_r_bm_recursion(add_bm, reset_bm, nnh_bp) {
    modify_field(bier_frr_metadata.add_bm, bier_frr_metadata.add_bm | add_bm);
    modify_field(bier_frr_metadata.reset_bm, bier_frr_metadata.reset_bm | reset_bm);

    modify_field(bier_frr_metadata.needs_recursion, 1);
    //clear des nnh_bp Bits aus dem BitString
    modify_field(bier_frr_metadata.BitString, bier_frr_metadata.BitString & ~ (1 << (nnh_bp - 1)));
}

table btaft {
    reads {
        bier_frr_metadata.bp: exact;
        bier_frr_metadata.BitString: ternary;
    }
    actions {
        a_r_bm_recursion; //Betrachte nächsten Eintrag und verbinde bisherige bm mit den neuen
        a_r_bm_apply; //default action, falls kein Hit in der BTAFT
    }
}


table print_ingress_start {
    reads {
        bier.BitString : exact;
    }
    actions {
        _drop;
    }
}

table print_ingress_end {
    reads {
        bier_frr_metadata.add_bm:exact;
        bier_frr_metadata.reset_bm : exact;
        bier[0].BitString : exact;
        bier[1].BitString : exact;
        bier_frr_metadata.flow_affected:exact;
        bier[0].Proto:exact;
        bier[1].Proto:exact;
        bier_metadata.BitString_of_interest:exact;
    }
    actions {
        _drop;
    }
}

table print_egress_start {
    reads {
        bier_frr_metadata.add_bm:exact;
        bier_frr_metadata.reset_bm : exact;
        bier[0].BitString : exact;
        bier[1].BitString : exact;
        bier_frr_metadata.flow_affected:exact;
        bier[0].Proto:exact;
        bier[1].Proto:exact;
        bier_metadata.BitString_of_interest:exact;
    }
    actions {
        _drop;
    }
}

table print_egress_end {
    reads {
        bier_frr_metadata.add_bm:exact;
        bier_frr_metadata.reset_bm : exact;
        bier[0].BitString : exact;
        bier[1].BitString : exact;
        bier_frr_metadata.flow_affected:exact;
        bier[0].Proto:exact;
        bier[1].Proto:exact;
        bier_metadata.BitString_of_interest:exact;
        bier_metadata.needs_cloning:exact;
        bier_frr_metadata.needs_recursion:exact;
        bier_frr_metadata.needs_cloning:exact;
    }
    actions {
        _drop;
    }
}

action save_frr_bitstring() {
    modify_field(bier_frr_metadata.BitString, bier.BitString);
}
table frr_copy_bitstring {
    actions {
        save_frr_bitstring;
    }
}

action save_bits_of_interest(bits_of_interest) {
    modify_field(bier_metadata.bits_of_interest, bits_of_interest);
    modify_field(bier_metadata.BitString_of_interest, bier.BitString & bits_of_interest);
    /*
        alle bits of interest müssen aus dem BitString gelöscht werden.
        Weitere Verarbeitung auf Basis des BitString_of_interest.
    */
    modify_field(bier.BitString, bier.BitString & ~ bits_of_interest);
    /* save BitString for when the header needs to be reconstructed */
    modify_field(bier_metadata.bs_remaining, bier.BitString);
}
table get_bits_of_interest {
    reads {
        bier.BitString : lpm;
    }
    actions {
        save_bits_of_interest;
    }
}

/*
WORKAROUND für clone_e2i
Aufruf von clone_e2e mit clone_spec 1
Dazu muss ein Mapping von clone_spec auf einen egress_port eingetragen
werden.
*/
action do_cloning() {
    clone_egress_pkt_to_egress(1, bier_FL);
}
table do_cloning_table {
    reads {
        standard_metadata.instance_type: exact;
    }
    actions {
        do_cloning;
    }
}

action frr_recursion() {
    modify_field(bier_metadata.needs_cloning, 0);
    recirculate(bier_FL);
}
table do_frr_recursion {
    actions {
        frr_recursion;
    }
}

/*
WORKAROUND für clone_e2i
Zurücksetzen des needs_cloning bits
Anpassen des BIER BitStrings
Recirculation des Pakets zum Ingress
*/
action do_clone_recirculation() {
    modify_field(bier_metadata.needs_cloning, 0);
    modify_field(bier.BitString, bier_metadata.bs_remaining);
    recirculate(bier_FL);
}
table do_clone_recirculation_table {
    reads {
        standard_metadata.instance_type : exact;
    }
    actions {
        do_clone_recirculation;
    }
}

/*
BIER Header wird wieder angefügt, etherType wird angepasst sowie das decap
flag züruckgesetzt
*/
action do_restore_bier() {
    add_header(bier);
    modify_field(bier.BitString, bier_metadata.bs_remaining);
    modify_field(bier_metadata.decap, 0);
    modify_field(ethernet.etherType, 0xBBBB);
}
table do_restore_bier_table{
    actions {
        do_restore_bier;
    }
}

action remove_outer_bier_header() {
    //copy_header(bier[0], bier[1]);
    remove_header(bier[0]);
    //reset metadata
    modify_field(bier_metadata.bits_of_interest, 0);

    modify_field(bier_metadata.decap, 0);
}
table do_remove_outer_bier_header {
    actions {
        remove_outer_bier_header;
    }
}

/*
Falls ein Paket die Domain verlassen soll, muss der etherType
zurückgesetzt werden und der BIER Header entfernt werden.
*/
action do_decap() {
    modify_field(ethernet.etherType, 0x0800);
    remove_header(bier);
}
table do_decap_table {
    actions {
        do_decap;
    }
}

action handover_mc_overlay() {
    /* multicast overlay */
    modify_field(intrinsic_metadata.mcast_grp, 1);
}   
table do_handover_mc_overlay {
    actions {
        handover_mc_overlay;
    }
}

action _drop() {
    drop();
}

action forward_connected(nbr_port) {
    /* Auf 0 setzen der bit_pos, die bearbeitet wurde */
    modify_field(bier_metadata.BitString_of_interest, bier_metadata.BitString_of_interest & ~ (1 << (bier_metadata.bit_pos - 1)));
    /*
    Markieren des Pakets, damit es später geklont wird
    */
    modify_field(bier_metadata.needs_cloning, 1);
    /*
    Setze die fürs Forwarding benötigten Daten
    */
    modify_field(standard_metadata.egress_spec, nbr_port);
}
action local_decap() {
    modify_field(bier_metadata.BitString_of_interest, bier_metadata.BitString_of_interest & ~ (1 << (bier_metadata.bit_pos - 1)));
    /*
    constraint: Fest an Port 1 schicken
    */
    //modify_field(standard_metadata.egress_spec, 1);
    modify_field(bier_metadata.needs_cloning, 1);

    /*
    Paket muss entsprechend markiert werden, damit der Header später
    entfernt wird
    */
    modify_field(bier_metadata.decap, 1);
}
table bift {
    reads {
        bier_metadata.bit_pos: exact;
    }
    actions {
        local_decap;
        forward_connected;
    }
}

/*
Fügt den BIER Header hinzu und setzt den BitString entsprechen.
Dann wird der etherType angepasst um das Paket zu markieren.
Zum Schluss wird das Paket wieder in den Ingress eingefügt, um die normale
BIER Paket Verarbeitung zu beginnen.
*/
action add_bier_header(bitstring) {
    add_header(bier);
    modify_field(bier.BitString, bitstring);
    modify_field(ethernet.etherType, 0xBBBB);
    modify_field(bier.Proto, 0x08);
    recirculate(bier_FL);
}
table bier_ingress {
    reads {
        ipv4.dstAddr : exact;
    }
    actions {
        add_bier_header;
        _drop;
    }
}

/*
Field List für die Felder, die bei der recirculation bzw. beim clone
erhalten bleiben sollen.
*/
field_list bier_FL {
    /*ethernet;*/
    /*bier;*/
    /*ipv4;*/
    /*bier;*/
    bier_metadata;
    standard_metadata;
    bier_frr_metadata;
}

/*
workaround zum Finden der Position der ersten 1 im BitString_of_interest
Sollte der BitString = 0 sein, wird kein Match gefunden und das Paket
entsprechend verworfen.
*/
action save_bit_pos(bit_pos) {
    modify_field(bier_metadata.bit_pos, bit_pos);
}
table find_bit_pos {
    reads {
        bier_metadata.BitString_of_interest : ternary;
    }
    actions {
        save_bit_pos;
        _drop;
        /* default action sollte drop sein, dann wird ein BS der nur aus 0en besteht direkt verworfen */
    }
}
