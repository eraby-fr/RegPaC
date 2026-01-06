# WebDashboard Docker Image

Dockerfile pour créer une image Docker légère du WebDashboard RegPaC, compatible Raspberry Pi 3B (ARMv7).

## Caractéristiques

- **Build stage**: `python:3.11-slim-bookworm` avec Node.js 18.x LTS pour compiler l'application Vite/React
- **Runtime stage**: `nginx:1.25-alpine` - serveur web léger avec reverse proxy
- **Reverse proxy**: Les requêtes `/api/*` sont automatiquement proxifiées vers le backend RegPaC
- **Compatible**: Raspberry Pi 3B (ARM32v7) et autres architectures
- **Port**: 80

## Build de l'image

Depuis la racine du projet RegPaC :

```bash
docker build -f Deployement/WebDashboard/dockerfile -t regpac-webdashboard:latest .
```

## Lancement du container

```bash
docker run -d \
  --name regpac-web \
  -p 80:80 \
  --restart unless-stopped \
  regpac-webdashboard:latest
```

Le dashboard sera accessible sur `http://localhost:80`

## Configuration du reverse proxy

Le fichier `nginx.conf` configure le reverse proxy pour rediriger les requêtes `/api/*` vers le backend RegPaC sur `http://192.168.0.3:7654`.

Si votre backend est sur une autre adresse, modifiez la ligne suivante dans `nginx.conf` :

```nginx
proxy_pass http://192.168.0.3:7654/;
```

## Build multi-architecture (optionnel)

Pour builder pour Raspberry Pi depuis une autre architecture :

```bash
docker buildx build \
  --platform linux/arm/v7 \
  -f Deployement/WebDashboard/dockerfile \
  -t regpac-webdashboard:latest \
  .
```

## Notes

- **Multi-stage build** : L'image utilise un build en deux étapes pour optimiser la taille finale
- **Build stage** : Python + Node.js pour compiler l'application React/Vite
- **Runtime stage** : Nginx seulement pour un runtime léger
- **Reverse proxy intégré** : Nginx proxifie automatiquement `/api/*` vers le backend, évitant les problèmes CORS
- Les fichiers statiques sont servis depuis `/app/dist`
- Headers no-cache configurés pour éviter les problèmes de mise à jour du cache
