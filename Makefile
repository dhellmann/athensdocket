# Build the CSS and JS files from bootstrap
# then move them into the right location.
.PHONY: bootstrap
bootstrap:
	rm -rf twitter-bootstrap-*/bootstrap
	(cd twitter-bootstrap-* && make bootstrap)
	rsync -av twitter-bootstrap-*/bootstrap docket/server/static
	rm -rf twitter-bootstrap-*/bootstrap
