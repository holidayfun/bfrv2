#include "includes/headers.p4"
#include "includes/parser.p4"

metadata routing_metadata_t routing_metadata;
header_type routing_metadata_t {
    fields {
        nhop_ipv4 : 32;
    }
}
metadata bier_metadata_t bier_metadata;
header_type bier_metadata_t {
    fields {
        k_pos : 4;
        drop : 1;
        bs_dest : 16;
        bs_remaining: 16;
    }
}

control ingress {
    if(ethernet.etherType == 0xBBBB) {
        /* received a BIER packet */ 
        /* Falls BS nur aus 0en besteht, verwerfen */
        if(bier.BitString == 0) {
            /* markiere Paket zum drop */
            /* (wird bei find_pos mitbehandelt */
        }

        /* Finde Position k der ersten 1 im BS */
        /* -> workaround mit find_pos möglich */
        /* soll die Position in Metadaten festhalten, falls kein Hit vorliegt, besteht BitString nur aus 0en => drop action  */
        apply(find_pos);
        
        /* Falls k der eigenen BFR-id entspricht, weiter geben an multicast overlay*/
        /* prüfen evtl mit einer Tabelle mit nur dem Eintrag der eigenen BFR-id, falls ein match auftritt, ist k identisch der BFR-id */
        apply(check_bfr_id){
            hit {
                /* Übergabe an multicast overlay, cleare Bit k und beginne von vorne */
            }
        }

        /* Nutze die BFR-id k als lookup key für die Bit Index Forwarding Table, erhalte als Rückgabe die F-BM und den Nachbarn NBR (evtl als Port?) */
        apply(bift);
        
        /* Bearbeitung des Packets geschieht in der Action zu bift */ 
    
    } else if(ethernet.etherType == 0x0800) {
        /* received a IPv4 packet. Check if it should be encapsulated in a BIER packet */
        apply(bier_ingress) {
            miss {
                /* normal ip forwarding on miss */
                apply(ipv4_lpm);
                apply(forward);
            }
            hit {
                /* BIER header was added, just recirculate it to the ingress to begin normal BIER processing */
            }
        }
    }
}

control egress {
    if (1 == 1) {

    } else {
        apply(send_frame);
    }
}

action _drop() {
    drop();
}

action bift_action(f_bm, nbr_port) {
         /* Packet klonen in p1 und p2 */
        /* Berechne p1.BitString AND F-BM um die Empfänger über NBR zu bestimmen, setze den BitString entpsrechend und schicke Paket an NBR */

        /* Berechne p1.BitString AND NOT F-BM, also cleare alle 1en im BS, die in der Maske gesetzt waren.
    Verschiebe dieses Paket zurück in die Ingress Pipeline und beginne von vorn */
    
    modify_field(bier_metadata.bs_dest, bier.BitString & f_bm);
    modify_field(bier_metadata.bs_remaining, bier.BitString & ~ f_bm);
    modify_field(standard_metadata.egress_spec, nbr_port);
}

table bift {
    reads {
        bier_metadata.k_pos: exact;
    }
    actions {
        bift_action;
    }
}

table check_bfr_id {
    reads {
        bier_metadata.k_pos : exact;
    }
    actions {
        /* Weiterleitung an multicast overlay */
        _drop;
    }
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

action add_bier_header(bitstring) {
    add_header(bier);
    modify_field(bier.BitString, bitstring);
    /* recirculate the paket to the ingress */
    /*recirculate(bier_field_list);*/
    
    
    /* some hard coded stuff */
    modify_field(standard_metadata.egress_spec, 3);
    modify_field(ethernet.dstAddr, 0xaaaa00000002);
    modify_field(ethernet.etherType, 0xBBBB);
}

/* recirculation takes a field list as parameter */
field_list bier_field_list {
    bier;
}


/* standard ip routing begin */
action set_nhop(nhop_ipv4, port) {
    modify_field(routing_metadata.nhop_ipv4, nhop_ipv4);
    modify_field(standard_metadata.egress_spec, port);
    add_to_field(ipv4.ttl, -1);
}
table ipv4_lpm {
    reads {
        ipv4.dstAddr : lpm;
    }
    actions {
        set_nhop;
        _drop;
    }
    size: 1024;
}

action set_dmac(dmac) {
    modify_field(ethernet.dstAddr, dmac);
}
table forward {
    reads {
        routing_metadata.nhop_ipv4 : exact;
    }
    actions {
        set_dmac;
        _drop;
    }
    size: 512;
}

action rewrite_mac(smac) {
    modify_field(ethernet.srcAddr, smac);
}
table send_frame {
    reads {
        standard_metadata.egress_port: exact;
    }
    actions {
        rewrite_mac;
        _drop;
    }
    size: 256;
}
/* standard ip routing end */


/* normal multicast begin */
/*
metadata intrinsic_metadata_t intrinsic_metadata;
table multicast_assoc {
    reads {
        ipv4.dstAddr : exact;
    }
    actions {
        set_mc_group;
        _drop;
    }
}
action set_mc_group(group_id) {
    modify_field(intrinsic_metadata.mcast_grp, group_id);
}
table send_mc {
    reads {
        intrinsic_metadata.mcast_grp : exact;
        standard_metadata.egress_port: exact;
        ipv4.dstAddr : exact;
    }
    actions{
        set_receiver;
        _drop;
    }
    size:256;
}
action set_receiver(ip, dmac) {
    modify_field(ipv4.dstAddr, ip);
    modify_field(ethernet.dstAddr, dmac);
} */
/* normal multicast end */

/* workaround to find pos k of first 1 in bitstring */
action save_pos(pos) {
    modify_field(bier_metadata.k_pos, pos);
}

table find_pos {
    reads {
        /* normally read bit string*/
        ipv4.ttl : lpm;
    }
    actions {
        save_pos;

        /* default action sollte drop sein, dann wird ein BS der nur aus 0en besteht direkt verworfen */
    }
}
