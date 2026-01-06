# RegPaC Dashboard

Tableau de bord moderne et responsive pour le système de contrôle de chauffage RegPaC.

## Fonctionnalités

- 📊 **Visualisation en temps réel** des températures de tous les capteurs
- 🔥 **Statut du chauffage** avec indicateur visuel
- ⚙️ **Configuration des consignes** pour les heures creuses et pleines
- 📱 **Design responsive** compatible mobile, tablette et desktop
- 🔄 **Actualisation automatique** toutes les 10 secondes

## Installation

```bash
cd WebDashboard
npm install
```

## Développement

```bash
npm run dev
```

Le dashboard sera accessible sur `http://localhost:3000`

**Note:** Le backend Flask doit être en cours d'exécution sur le port 80 pour que l'API fonctionne.

## Build pour la production

```bash
npm run build
```

Les fichiers de production seront générés dans le dossier `dist/`.

## Configuration

Le fichier `vite.config.js` contient un proxy configuré pour rediriger les appels API vers le backend Flask:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:80',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```

Modifiez l'URL cible si votre backend Flask est sur un autre hôte ou port.

## Stack Technique

- **React 18** - Framework UI
- **Vite** - Build tool et dev server
- **TailwindCSS** - Framework CSS utility-first
- **Lucide React** - Icônes modernes
- **API REST** - Communication avec le backend Flask

## Architecture

```
WebDashboard/
├── src/
│   ├── App.jsx          # Composant principal
│   ├── main.jsx         # Point d'entrée React
│   └── index.css        # Styles globaux avec TailwindCSS
├── index.html           # Template HTML
├── package.json         # Dépendances npm
├── vite.config.js       # Configuration Vite
├── tailwind.config.js   # Configuration TailwindCSS
└── postcss.config.js    # Configuration PostCSS
```

## API Endpoints utilisés

- `GET /temperatures` - Récupère les températures de tous les capteurs
- `GET /heater/status` - Récupère le statut du chauffage (ON/OFF)
- `GET /setpoint` - Récupère les consignes de température
- `POST /setpoint` - Met à jour les consignes de température

## Personnalisation

### Couleurs

Les couleurs principales peuvent être modifiées dans `tailwind.config.js`:

```javascript
colors: {
  primary: {
    // Personnalisez vos couleurs ici
  }
}
```

### Fréquence d'actualisation

Dans `App.jsx`, modifiez l'intervalle (en millisecondes):

```javascript
const interval = setInterval(fetchData, 10000) // 10 secondes
```
