# Makefile

.PHONY: ast json xml test copy zip

ast:
	python src/parse.py < test/test-main.txt > test/ast.py

json:
	python src/parse.py < test/test-main.txt > test/ast.json

xml:
	python src/parse.py < test/test-main.txt > test/ast.xml

test:
	python src/parse.py < test/test.txt

copy:
	cp src/parse.py tests/

zip:
	zip -j xprochp00 src/parse.py doc/readme1.md
