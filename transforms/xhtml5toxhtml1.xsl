<?xml version="1.0" encoding="UTF-8"?>

<!-- Backports a XHTML 5 document to XHTML 1.0.
Following features are backported:
- sections and articles to the usual h1-h7 with divs
  (Limitation: Only h1, no hn with n>1 must be used in the XHTML 5 source)
- doctype


The output is also valid HTML 4.01 (see
http://www.w3.org/TR/xhtml1/#guidelines), but consider the following:
- Most things mentioned in http://www.w3.org/TR/xhtml1/#guidelines are
  not taken care of.
- no meta element to indicate the charset is generated. Instead, the
  server should be configured to send correct headers.
- Every attribute xml:lang is duplicated into a lang.

Open problems:
- Do XSLT processors output CDATA sections automatically? Would not
  work in HTML 4.01.
-->

<xsl:stylesheet
    version = "1.0"
    xmlns:xsl   = "http://www.w3.org/1999/XSL/Transform"
    xmlns:fn    = "http://www.w3.org/2005/xpath-functions"
    xmlns:html  = "http://www.w3.org/1999/xhtml"
    xmlns       = "http://www.w3.org/1999/xhtml"
    exclude-result-prefixes="xsl fn html"
>

<xsl:output
     method="xml"
     doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN"
     doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"
     encoding="UTF-8"
     indent="yes" />

<xsl:template match="html:head">
    <xsl:copy>
        <xsl:apply-templates select="@*"/>
        <!--<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>-->
        <xsl:apply-templates select="node()"/>
    </xsl:copy>
</xsl:template>

<xsl:template match="html:meta[@charset]"></xsl:template>

<xsl:template match="@xml:lang">
    <xsl:copy/>
    <attribute name="lang"><xsl:value-of select="."/></attribute>
</xsl:template>

<xsl:template match="html:section|html:article">
    <div>
        <xsl:apply-templates select="@*|node()"/>
    </div>
</xsl:template>

<xsl:template match="html:h1">
    <xsl:element name="{concat('h',string(count(ancestor::html:section|ancestor::html:article|ancestor::html:body)))}">
        <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
</xsl:template>

<xsl:template match="html:h2|html:h3|html:h4|html:h5|html:h6|html:h7">
    <xsl:message><xsl:value-of select="local-name()"/> found, but only h1
    supported for the outline computation.</xsl:message>
    <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
</xsl:template>

<!-- Identity transformation -->

<xsl:template match="@*|node()">
    <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
</xsl:template>

</xsl:stylesheet>
