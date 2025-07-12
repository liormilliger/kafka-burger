mkdir -p burger-app/{producer,kitchen,delivery,payment,storage,shared} && \
touch burger-app/{docker-compose.yaml,.env} && \
touch burger-app/producer/{Dockerfile,producer.py} && \
touch burger-app/kitchen/{Dockerfile,kitchen.py} && \
touch burger-app/delivery/{Dockerfile,delivery.py} && \
touch burger-app/payment/{Dockerfile,payment.py} && \
touch burger-app/storage/{Dockerfile,storage.py} && \
touch burger-app/shared/menu.py

