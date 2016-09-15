#include "includes/headers.p4"
#include "includes/parser.p4"

action _drop() {
    drop();
}

header_type routing_metadata_t {
    fields {
        nhop_ipv4 : 32;
    }
}

metadata routing_metadata_t routing_metadata;
/* Metadata for Multicast */
metadata intrinsic_metadata_t intrinsic_metadata;

/* Table for associating a IP to a Multicast group ID */
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


action set_nhop(nhop_ipv4, port) {
    modify_field(routing_metadata.nhop_ipv4, nhop_ipv4);
    modify_field(standard_metadata.egress_port, port);
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


table bier_packet {
    reads {
	ipv4.dstAddr : lpm;
    }
    actions {
    	_drop;
    }
    size: 256;
}


control ingress {
    apply(multicast_assoc);
    apply(ipv4_lpm);
    apply(forward);
}

control egress {
    apply(send_frame);
}
