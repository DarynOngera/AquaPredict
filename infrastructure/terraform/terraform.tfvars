# OCI Authentication
tenancy_ocid     = "ocid1.tenancy.oc1..aaaaaaaauonpamdensfckzkffpfco5xovo2tukr6qwdkdj3jikqti3etopxq"
user_ocid        = "ocid1.user.oc1..aaaaaaaagvy54stujunh423tnqop7dtqbewpvefdrstw352fhgqaazmoegra"
fingerprint      = "e6:94:2f:ef:75:48:5c:92:a0:b2:fa:11:3d:08:e4:dc"
private_key_path = "~/.oci/oci.pem"
region           = "eu-frankfurt-1"
compartment_ocid = "ocid1.compartment.oc1..aaaaaaaa3shmzzlzhvp5otznv3lcjfooc2iui7wuutysdu26oywufqkasxiq"

# Availability Domain (get from: oci iam availability-domain list)
availability_domain = "dRkB:EU-FRANKFURT-1-AD-1"

# Network Configuration
vcn_cidr = "10.0.0.0/16"

# Database Configuration
db_name           = "aquapredict"
db_admin_password = "#AquaPredict2025!"  # Must meet complexity requirements
db_wallet_password = "WalletSecure2025!"
db_app_user       = "aquapredict_app"
db_app_password   = "AppUser2025!"
adb_cpu_core_count = 2
adb_storage_tb    = 1
adb_is_free_tier  = false  # Set to true for Always Free tier (note: Always Free doesn't support private subnet)
adb_enable_auto_scaling = true
adb_create_database = false  # Disabled - feature not enabled for tenancy

# OKE Configuration
oke_cluster_name   = "aquapredict-cluster"
kubernetes_version = "v1.31.1"
oke_node_pool_size = 3
oke_node_shape     = "VM.Standard.E4.Flex"

# Compute Instance Configuration
compute_instance_shape     = "VM.Standard.E4.Flex"
compute_instance_ocpus     = 2
compute_instance_memory_gb = 16
compute_assign_public_ip   = false  # Private subnet doesn't allow public IPs
compute_create_load_balancer = true

# SSH Key (paste your public key here)
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDAADH6Gr48Iw4aBb411pQ5E2tga0PDOGvVF3FgCiV6c1uzcXmW5XyQ4x8oHlaxOlsHcf1XA7UVYbPloI3B2/2bvDNVvrf37cTQTBdxLP6xMcrK/8nBXefViy3IBs7/4zz0ptKosVlRLLDoBftNbQYihJJUULOzKXkqoJx4kg+6MGU6eygqDJf/44PM/D2dXXvjOd27ujjt9EZ6lulOd0HetVOI5EMjyNVH5VC84JIwVOAfFcsw5sqp85KtoOMpDkN9phPDstAHs/Hjanc+X0FWvfbq2pAuEfo4rTqYwbDYZL95Mrno7tA2x4p6JXQuv9OMIZmvo54CT/hQeRg8wETB opc@instance-20251002-0320"

# Google Earth Engine Service Account
# Paste the entire JSON content as a single line with escaped quotes
gee_service_account_json = "{\"type\":\"service_account\",\"project_id\":\"aquapredict-473718\",\"private_key_id\":\"62e7ad24e59dfd6639ebe3e66fdd9fdc0642eb4b\",\"private_key\":\"-----BEGIN PRIVATE KEY-----\\nMIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQC5VyGe13WTlUw5\\n54SXZgVOpsHW/CXxq25zs6Kpsjebxm/BPzRsxan7UTVlL86pYsvhRu3hYWotTuly\\njJO753LFd5QoUvPUkKat9N9IJOOIL4zXFAgEKvXNoT7vwkmDFJ0qxoQsWaagguGN\\npb2tY0YFhb36Gp+cziV4CEP9ZXr4Ks/E5VwNR6o1ye/Sagu1iWpm3fG+a+/j0JOJ\\n37Vd2MN/m2EE1o1xbn9ZBmNA8Vhosb3ZqPXC/rSG6VC4NSagEUxhBTKiADPTHdNh\\ne2CXF9kkT7RoWGEkCekdX7iBM4V+kXtrJptWY13sRZjlkWW0BSns1kqLduFIxjVk\\nOExOlSLzAgMBAAECgf87Xa1nM5x1qVzBL2dJF2SbzM5KDnoY7tByPxfbQzqMqwMg\\n4x3nuWi5F0oDH00S9JJZll6b0pgv6xbbmiu4BGq+1Y6fW/K+I5dAIS9j7Gz1MkXq\\nnn/y1c/mDcAbDCB/3Bp7mRq9GfpFb6bPuEcJQsMrAavYcK6vi1h1GjCs+dRpqMFX\\nMB5/EfAhrVI74K8qzVJ5PTJzsT7eAMj4hJTIlPnffEcpQTvsFASAz6orgAMOQeEI\\nmFby/hmL6X4f/SjjbkSOt4R0cGDZ3DkrOBxislmc57dSCYks06Qfg72oY8OlYkwQ\\nSLfXikj+AaZ5E94B1rgcSCfgaHq5vFizneQ2N0ECgYEA3CuLs7YYm3vKEQB76zVe\\nbv6VwDZnhSzT1Ux+ExwHbOqwvGARUHSR52E5fIh2WOUdH6+6rhZn6jrE95z+3yiC\\nQSUnHUU4eRuwTKfV1atKlwjiv0NeXaC/0uwyiMuTZKi3uKxPwkr6LCJ8etWPoZps\\nUhiO2BllVMz9YGhGY+DibwMCgYEA14CNS6rixkrPoKi5TzCZ2DSUJgIeVjx0doQ9\\nkbTSFrjwam4Ir/KFXfU2hf/FW3ACFwL8uXy4+pDJsGfB4NNfuhmS7D2yZYS7V84e\\nbO+GR2JvDWpt+Xvp4UaLRQZjfmHgLp3OKdJozDlD/VipShRFZ5j1cfNuGI3YN4Vs\\n7zUrAVECgYEAyiWBIwNyHG/P20RiglaB2c8Nl2lcKr450IFm0AzQFIR2uL5Lp18g\\nBx0RNvHkF0JlNw6Vi/kud7R13BLdP+9liIKgIxPHAgsWF4uRnZij54BVD96+6aAJ\\n/5K14ztmnOj7picvI+jLQXJ4cB9cvLeX9NhvbqICk5WSnc2fs1xrChkCgYBK3503\\n9w2He6Kb3UNVIjuxhMMcWYwUxjhonRWPNFXyExtkvwpBp29y76mb8PuvA0GWoTER\\neSYD2J5arhIMfSQ7UntbnSwIXY+BuFmV27q5vpd6/8lp7wWZgZsNxmR3GqZ7S9S/\\nbx1+Jz9aHJ3k4RokHl7Y0o0j9tRypebtTXm9oQKBgBIngUr6cX5Y7lKnZmwZ1g84\\nZKvqmlo7LNxf1Kc7v3CPDWUWVIwXLQCm+frhj9iB9MpZWqm7zTy0Bf7f3NJ9AKJ0\\ncR989L5Hqg+E55XFnrApHjI6HPRVzFUWGPhUYBqr8Gi0BiaeJ33/xdNo3az6sMik\\nwXqLu5aQnbqqYO+k6ZIi\\n-----END PRIVATE KEY-----\\n\",\"client_email\":\"aquapredict@aquapredict-473718.iam.gserviceaccount.com\",\"client_id\":\"108376993946489423309\",\"auth_uri\":\"https://accounts.google.com/o/oauth2/auth\",\"token_uri\":\"https://oauth2.googleapis.com/token\",\"auth_provider_x509_cert_url\":\"https://www.googleapis.com/oauth2/v1/certs\",\"client_x509_cert_url\":\"https://www.googleapis.com/robot/v1/metadata/x509/aquapredict%40aquapredict-473718.iam.gserviceaccount.com\",\"universe_domain\":\"googleapis.com\"}"

# Data Science Configuration
ds_deploy_models = false  # Set to true to deploy models to endpoints

# Environment
environment = "production"
