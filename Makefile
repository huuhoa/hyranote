clean:
	rm -rf build dist hyranote.egg-info

sdist:
	python3 setup.py sdist bdist_wheel

upload:
	python3 -m twine upload dist/* --verbose
