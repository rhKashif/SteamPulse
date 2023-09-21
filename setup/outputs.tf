output "RDS_address" {
  description = "RDS Endpoint Address"
  value       = aws_db_instance.steampulse_database.address
}

output "Static_IP" {
  description = "Static IP address for Streamlit Dashboard"
  value =  aws_eip.steampulse_lb_elastic_ip.public_ip
}