@echo off
echo Starting MinIO server with Docker...

docker run --rm -d --name minio ^
  -p 9000:9000 ^
  -p 9001:9001 ^
  -e MINIO_ROOT_USER=minioadmin ^
  -e MINIO_ROOT_PASSWORD=minioadmin ^
  quay.io/minio/minio server /data --console-address ":9001"

echo MinIO should now be running on:
echo - S3 Endpoint: http://localhost:9000
echo - Console UI : http://localhost:9001


rclone config create test_server_s3 s3 ^
  provider Minio ^
  env_auth false ^
  access_key_id minioadmin ^
  secret_access_key minioadmin ^
  endpoint http://localhost:9000 ^
  region us-east-1