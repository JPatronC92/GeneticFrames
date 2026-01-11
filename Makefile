.PHONY: dev test clean zoo-status

# 🐳 Development
dev:
	@echo "🚀 Starting GeneticFrames Zoo..."
	docker-compose up --build

# 🧪 Testing
test:
	@echo "🧪 Running Backend Tests..."
	cd geneticframes-api && pip install -r requirements.txt && pytest

# 🧹 Cleaning
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf geneticframes-web/dist
	@echo "✅ Clean complete."

# 🦁 Status
zoo-status:
	@echo "📡 Connecting to Zoo Control Center..."
	@python3 scripts/zoo_status.py || echo "⚠️  Make sure 'make dev' is running first!"
