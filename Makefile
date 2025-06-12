# Makefile

.PHONY: ast json xml test copy zip

ast:
	python src/parse.py < test/test.txt > test/ast.py

json:
	python src/parse.py < test/test.txt > test/ast.json

xml:
	python src/parse.py < test/test.txt > test/out.xml

test:
	python src/parse.py < test/test.txt

copy:
	cp src/parse.py tests/

zip:
	zip -j xprochp00 src/parse.py docs/readme1.pdf
