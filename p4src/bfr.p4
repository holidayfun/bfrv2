#include "includes/headers.p4"
#include "includes/parser.p4"

metadata routing_metadata_t routing_metadata;
header_type routing_metadata_t {
    fields {
        nhop_ipv4 : 32;
    }
}

control ingress {
    apply(bier_ingress) {
        miss {
            /* normal ip forwarding on miss */
            apply(ipv4_lpm);
            apply(forward);
        }
    }
}

control egress {
    apply(send_frame);
}


action _drop() {
    drop();
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
action dump_pos(pos) {
    modify_field(standard_metadata.egress_port, pos);
}
table find_pos {
    reads {
        /* normally read bit string*/
        ipv4.ttl : lpm;
    }
    actions {
        dump_pos;
    }
}
