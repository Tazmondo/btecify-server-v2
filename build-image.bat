docker login
docker buildx build -t tazmondo/btecify-server --platform linux/amd64,linux/arm64 --push .
