# Nexus MCP Server Documentation

This directory contains the HTML documentation for Nexus MCP Server, designed for GitHub Pages deployment.

## 🚀 Quick Start

1. **Enable GitHub Pages** in your repository settings
2. **Set source** to `/docs` folder
3. **Access documentation** at `https://yourusername.github.io/nexus-mcp-server/`

## 📁 Structure

```
docs/
├── index.html              # Main documentation homepage
├── assets/
│   ├── css/
│   │   └── main.css        # Main stylesheet with themes
│   ├── js/
│   │   └── main.js         # Interactive functionality
│   └── images/             # Screenshots and assets
└── pages/
    ├── setup-vscode.html   # VS Code setup guide
    ├── setup-claude.html   # Claude Desktop setup
    ├── dynamic-tools.html  # Dynamic tool creation
    ├── tools-overview.html # Complete tools overview
    └── ...                 # Additional documentation pages
```

## ✨ Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark/Light Themes**: Automatic theme switching
- **Search Functionality**: Built-in documentation search
- **Syntax Highlighting**: Code blocks with syntax highlighting
- **Interactive Navigation**: Smooth scrolling and active section highlighting
- **Mobile-Friendly**: Optimized for all screen sizes

## 🎨 Customization

### Theme Colors
Edit `assets/css/main.css` to customize the color scheme:

```css
:root {
  --primary-color: #2563eb;
  --secondary-color: #1e40af;
  --accent-color: #3b82f6;
  /* ... */
}
```

### Adding Pages
1. Create new HTML file in `pages/` directory
2. Use existing page as template
3. Update navigation in all pages
4. Add to table of contents

## 🔧 Development

### Local Testing
```bash
# Simple HTTP server
python -m http.server 8000

# Navigate to http://localhost:8000
```

### Live Reload (Optional)
```bash
# Using live-server (npm install -g live-server)
live-server docs/
```

## 📱 Browser Support

- Chrome/Chromium 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Update documentation
4. Test on multiple devices
5. Submit pull request

## 📝 License

Same as parent project - see main README.md for details.