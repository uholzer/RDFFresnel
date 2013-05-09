#!/usr/bin/env python

import sys
from distutils.core import setup

if not sys.version_info >= (3,2):
    print("Error: RDFFresnel requires at least Python 3.2.")
    exit(1)

setup(name='RDFFresnel',
      version='0.1',
      description='RDF Fresnel Renderer for RDFLib',
      author='Urs Holzer',
      author_email='urs@andonyar.com',
      url='https://github.com/uholzer/RDFFresnel',
      packages=['RDFFresnel'],
      scripts=['scripts/rdffresnel-render'],
      data_files=[
            ('share/RDFFresnel/transforms', [
                'transforms/fresnelprettyprint.xsl',
                'transforms/fresnelsort.xsl', 
                'transforms/fresneltoxhtml5.xsl', 
                'transforms/xhtml5tohtml5.xsl', 
                'transforms/xhtml5toxhtml1.xsl'
            ])
      ],
      keywords=['Requires: rdflib'],
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Natural Language :: English",
      ]
     )

