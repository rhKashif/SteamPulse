output "RDS_address" {
  description = "RDS Endpoint Address"
  value       = aws_db_instance.steampulse_database.address
}