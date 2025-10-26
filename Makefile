.PHONY: install

install:
	sudo apt update && sudo apt upgrade -y
	sudo apt-get install tmux
	# re use picamera2 from the system 
	uv venv --system-site-packages
	uv sync

.PHONY: install-dev
install-dev:
	make install
	uv sync --dev

.PHONY: run
run:
	uv run catflap-detector

.PHONY: run-bg
run-bg:
	nohup uv run catflap-detector &

.PHONY: logs
logs:
	tail -f runtime/logs/main_app.log

.PHONY: clean-logs
clean-logs:
	rm -f runtime/logs/*.log