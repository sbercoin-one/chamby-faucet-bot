FROM node:18-alpine

WORKDIR /app

COPY package.json .

RUN npm install

COPY signing_service.js .

EXPOSE 5000

CMD ["node", "signing_service.js"]
