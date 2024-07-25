PLUGIN_NAME=iadb_toolbox

LANG_PATH=i18n
LANG_SOURCES=$(wildcard $(LANG_PATH)/*.ts)
LANG_FILES=$(patsubst $(LANG_PATH)/%.ts, $(LANG_PATH)/%.qm, $(LANG_SOURCES))

PRO_PATH=.
PRO_FILES=$(wildcard $(PRO_PATH)/*.pro)

ts: $(PRO_FILES)
	pylupdate5 -verbose $<

qm: $(LANG_SOURCES)
	lrelease $<

clean:
	find -name "*.qm" -exec rm -r {} \;
	find -name "__pycache__" -type d -exec rm -r {} \; -prune
	rm -f $(PLUGIN_NAME).zip

package: clean
	git archive -9 --prefix=$(PLUGIN_NAME)/ --output=$(PLUGIN_NAME).zip HEAD

upload: package
	plugin_uploader.py $(PLUGIN_NAME).zip
