# 🤝 Contributing Guide

Thank you for considering contributing to our AppSumo products!

## How to Contribute

### 1. Bug Reports
- Use GitHub Issues
- Include product name
- Describe expected vs actual behavior
- Add steps to reproduce
- Include environment details

### 2. Feature Requests
- Open an issue first
- Explain use case
- Describe expected behavior
- Consider AppSumo tier implications

### 3. Code Contributions

**Before starting**:
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Follow our code style

**Code Style**:
- Python: PEP 8, type hints
- JavaScript: ESLint, Prettier
- Commits: Conventional commits

**Testing**:
```bash
# Backend
cd backend
pytest

# Frontend  
cd frontend
npm test
```

**Pull Request**:
1. Update documentation
2. Add tests
3. Ensure CI passes
4. Request review

## Development Setup

```bash
# Clone
git clone https://github.com/yourusername/appsumo-products

# Start product
cd appsumo-products/chatbot-pro
docker-compose up

# Or use scripts
./start-all.sh
```

## Questions?

- Email: dev@blocksigmakode.ai
- Discord: (coming soon)

## License

By contributing, you agree your contributions will be licensed under MIT License.
