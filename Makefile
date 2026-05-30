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

.PHONY: install-service
install-service:
	# Install the systemd service + watchdog/journald drop-ins (see deploy/README.md).
	# Fills the <USER>/<INSTALL_DIR> placeholders from the current user and repo path.
	sudo sed -e 's|<USER>|$(shell whoami)|g' -e 's|<INSTALL_DIR>|$(CURDIR)|g' \
		deploy/catflap-detector.service > /etc/systemd/system/catflap-detector.service
	sudo mkdir -p /etc/systemd/system.conf.d /etc/systemd/journald.conf.d
	sudo cp deploy/10-watchdog.conf /etc/systemd/system.conf.d/10-watchdog.conf
	sudo cp deploy/10-persistent.conf /etc/systemd/journald.conf.d/10-persistent.conf
	sudo systemctl daemon-reload
	sudo systemctl daemon-reexec
	sudo systemctl restart systemd-journald && sudo journalctl --flush
	sudo systemctl enable --now catflap-detector
	@echo "Installed. Check status with: systemctl status catflap-detector"

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