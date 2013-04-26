#!/usr/bin/env python

from distutils.core import setup

setup(name='RDFFresnel',
      version='0.1',
      description='RDF Fresnel Renderer for RDFLib',
      author='Urs Holzer',
      author_email='urs@andonyar.com',
      url='https://github.com/uholzer/RDFFresnel',
      packages=['RDFFresnel'],
      scripts=['scripts/rdffresnel-render'],
      keywords=['Requires: rdflib'],
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Natural Language :: English",
      ]
     )

