#include "includes/bier_te/headers.p4"
#include "includes/bier_te/parser.p4"
#include "includes/bier_te/ip_forwarding.p4"
#include "includes/bier_te/classic_mc.p4"


metadata routing_metadata_t routing_metadata;
metadata bier_metadata_t bier_metadata;
metadata intrinsic_metadata_t intrinsic_metadata;

control ingress {
    if(ethernet.etherType == 0xBBBB) {
        /* BIER Paket empfangen */
        apply(find_pos)
        {
            hit
            {
                apply(check_bfr_id)
                {
                    miss /* Bit entspricht nicht der eigenen BFR-id */
                    {
                        apply(bift);
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
}

control egress {
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
    } else if(bier_metadata.needs_cloning == 1 or bier_metadata.decap == 1) {
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
        apply(do_decap_table);
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

action _drop() {
    drop();
}

/*
    Bei einem Hit in der Bit Index Forwarding Table muss das Paket geklont
    werden und die BitStrings entsprechend angepasst werden.
    Das Cloning geschieht erst in der Egress Pipeline.
*/
action bift_action(f_bm, nbr_port) {
    modify_field(bier_metadata.bs_remaining, bier.BitString & ~ f_bm);
    /*
        Markieren des Pakets, damit es später geklont wird
    */
    modify_field(bier_metadata.needs_cloning, 1);
    /*
        Setze die fürs Forwarding benötigten Daten
    */
    modify_field(standard_metadata.egress_spec, nbr_port);
    modify_field(bier.BitString, bier.BitString & f_bm);
}

table bift {
    reads {
        bier_metadata.k_pos: exact;
    }
    actions {
        bift_action;
    }
}

/*
    Das Paket soll unter anderem an diesem BFR die Domain verlassen.
    Setze das Bit für diesen BFR auf 0 und reiche es an MC Overlay weiter.
*/
action packet_for_bfr(bm) {
    modify_field(bier_metadata.bs_remaining, bier.BitString & ~ bm);
    /*
        constraint: Fest an Port 1 schicken
    */
    modify_field(standard_metadata.egress_spec, 1);
    modify_field(bier_metadata.needs_cloning, 1);
    /*
        Paket muss entsprechend markiert werden, damit der Header später
        entfernt wird
    */
    modify_field(bier_metadata.decap, 1);
}

table check_bfr_id {
    reads {
        bier_metadata.k_pos : exact;
    }
    actions {
        /* Weiterleitung an multicast overlay */
        packet_for_bfr;
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
    bier_metadata;
    standard_metadata;
}

/*
    workaround zum Finden der Position der ersten 1 im BitString
    Sollte der BitString = 0 sein, wird kein Match gefunden und das Paket
    entsprechend verworfen.
*/
action save_pos(pos) {
    modify_field(bier_metadata.k_pos, pos);
}

table find_pos {
    reads {
        /* normally read bit string*/
        bier.BitString : lpm;
    }
    actions {
        save_pos;
        _drop;
        /* default action sollte drop sein, dann wird ein BS der nur aus 0en besteht direkt verworfen */
    }
}
