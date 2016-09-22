cli.py -s 1 < ip_forwarding/entries_s1
cli.py -s 2 < ip_forwarding/entries_s2
cli.py -s 3 < ip_forwarding/entries_s3

cli.py -s 1 < bier/bier_ingress
cli.py -s 2 < bier/bier_ingress
cli.py -s 3 < bier/bier_ingress

cli.py -s 1 < bier/find_pos
cli.py -s 2 < bier/find_pos
cli.py -s 3 < bier/find_pos


cli.py -s 1 < bier/bift_entries_s1
cli.py -s 2 < bier/bift_entries_s2
cli.py -s 3 < bier/bift_entries_s3

cli.py -s 1 < bier/check_bfr_id_entries_s1
cli.py -s 2 < bier/check_bfr_id_entries_s2
cli.py -s 3 < bier/check_bfr_id_entries_s3

cli.py -s 1 < bier/do_clone_recirculation_table
cli.py -s 1 < bier/do_cloning_table
cli.py -s 1 < bier/mirroring

cli.py -s 2 < bier/do_clone_recirculation_table
cli.py -s 2 < bier/do_cloning_table
cli.py -s 2 < bier/mirroring

cli.py -s 3 < bier/do_clone_recirculation_table
cli.py -s 3 < bier/do_cloning_table
cli.py -s 3 < bier/mirroring

cli.py -s 1 < bier/do_decap_table
cli.py -s 2 < bier/do_decap_table
cli.py -s 3 < bier/do_decap_table

cli.py -s 1 < bier/do_restore_bier_table
cli.py -s 2 < bier/do_restore_bier_table
cli.py -s 3 < bier/do_restore_bier_table
