<?xml version="1.0" encoding="UTF-8"?>

<!-- Create XHTML 5 from Fresnel result tree. This stylesheet is
suitable for import from another stylesheet, but can also be used
directly. -->

<xsl:stylesheet
    version = "1.0"
    xmlns:xsl   = "http://www.w3.org/1999/XSL/Transform"
    xmlns:fn    = "http://www.w3.org/2005/xpath-functions"
    xmlns:rdf   = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:foaf  = "http://xmlns.com/foaf/0.1/"
    xmlns:ft    = "http://www.andonyar.com/rec/2012/sempipe/fresnelxml"
    xmlns:xhtml = "http://www.w3.org/1999/xhtml"
    xmlns       = "http://www.w3.org/1999/xhtml"
    exclude-result-prefixes="xsl fn rdf foaf fres xhtml"
>

<xsl:output
     method="xml"
     encoding="UTF-8"
     indent="yes" />

<!-- Root element -->

<xsl:template match="/ft:fresnelresult">
    <html>
    <head>
        <title><xsl:value-of select="/ft:fresnelresult/ft:resource/ft:label"/></title>
        <style type="text/css"><![CDATA[
            @namespace html     "http://www.w3.org/1999/xhtml";
            .figure { float: right }
            html|p.otherinterface { font-size: 120%; font-weight: bold }
        ]]></style>
    </head>
    <body>
        <h1><xsl:apply-templates select="/ft:fresnelresult/ft:resource/ft:label"/></h1>
        <xsl:apply-templates select="ft:resource"/>
    </body>
    </html>
</xsl:template>

<!-- ft:resource -->

<xsl:template match="ft:resource[contains(@class,'html:dl')]">
    <xsl:apply-templates select="ft:property[contains(@class,'out-of-order:before')]"/>
    <dl>
    <xsl:apply-templates select="ft:property[not(contains(@class,'out-of-order'))]" mode="dl"/>
    </dl>
    <xsl:apply-templates select="ft:property[contains(@class,'out-of-order:after')]"/>
</xsl:template>

<xsl:template match="ft:resource" mode="img">
    <img src="{@uri}">
        <xsl:choose>
        <xsl:when test="string(ft:label)">
            <xsl:attribute name="alt"><xsl:value-of select="ft:label"/></xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
            <xsl:message>
                Attribute alt in image <xsl:value-of select="@uri"/>
                omitted because there is no label.
            </xsl:message>
        </xsl:otherwise>
        </xsl:choose>
    </img>
</xsl:template>

<xsl:template match="ft:resource">
    <!-- Should we place a label here too? -->
    <xsl:apply-templates select="ft:property"/>
</xsl:template>

<xsl:template match="ft:resource[not(ft:property)]">
    <xsl:apply-templates select="ft:label"/>
</xsl:template>

<xsl:template match="ft:resource[not(ft:property) and not(string(ft:label))]">
    <!-- Label is missing and no property is present, still we should
         show something. -->
    <xsl:value-of select="@uri"/>
</xsl:template>

<!-- ft:property -->

<xsl:template match="ft:property[contains(@class,'figure')]">
    <xsl:call-template name="contentBefore"/>
    <div class="{@class}">
    <xsl:apply-templates select="ft:label"/>
    <xsl:apply-templates select="ft:value"/>
    <xsl:call-template name="contentNoValue"/>
    </div>
    <xsl:call-template name="contentAfter"/>
</xsl:template>

<xsl:template match="ft:property">
    <xsl:call-template name="contentBefore"/>
    <xsl:apply-templates select="ft:label"/>
    <xsl:apply-templates select="ft:value"/>
    <xsl:call-template name="contentNoValue"/>
    <xsl:call-template name="contentAfter"/>
</xsl:template>

<xsl:template match="ft:property" mode="dl">
    <xsl:call-template name="contentBefore"/>
    <dt><xsl:apply-templates select="ft:label"/></dt>
    <xsl:for-each select="ft:value">
    <dd><xsl:apply-templates select="."/><xsl:call-template name="contentNoValue"/></dd>
    </xsl:for-each>
    <xsl:call-template name="contentAfter"/>
</xsl:template>

<!-- ft:value -->

<xsl:template match="ft:value[@type='literal']">
    <xsl:call-template name="contentBefore"/>
    <!-- We need to support arbitrary XML here, therefore we use
    copy-of instead of value-of. -->
    <xsl:copy-of select="(ft:literal|ft:xmlliteral)/child::node()"/>
    <xsl:call-template name="contentAfter"/>
</xsl:template>

<xsl:template match="ft:value[contains(@class,'html:section')]">
    <xsl:call-template name="contentBefore"/>
    <section>
        <h1><xsl:apply-templates select="ft:resource/ft:label"/></h1>
        <xsl:apply-templates select="ft:resource"/>
    </section>
    <xsl:call-template name="contentAfter"/>
</xsl:template>

<xsl:template match="ft:value[contains(@class,'html:img')]">
    <xsl:call-template name="contentBefore"/>
    <xsl:apply-templates select="ft:resource" mode="img"/>
    <xsl:call-template name="contentAfter"/>
</xsl:template>

<xsl:template match="ft:value">
    <xsl:call-template name="contentBefore"/>
    <xsl:apply-templates select="ft:resource"/>
    <xsl:call-template name="contentAfter"/>
</xsl:template>

<!-- ft:label -->

<xsl:template match="ft:label">
    <xsl:choose>
    <xsl:when test="not(string(.))">
        <xsl:value-of select="../@uri"/>
    </xsl:when>
    <xsl:otherwise>
        <xsl:value-of select="."/>
    </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- Additional content -->
<!-- IMPORTANT:
    I think it should be
    ../preceding-sibling::ft:property[1] or ../preceding-sibling::ft:value[1]
    instead of
    ../preceding-sibling::ft:property[2] or ../preceding-sibling::ft:value[2]
    I assume this to be a bug in libxml.
-->

<xsl:template name="contentBefore">
    <xsl:choose>
        <xsl:when test="ft:contentLast and not(preceding-sibling::ft:property[2] or preceding-sibling::ft:value[2])">
            <xsl:apply-templates select="ft:contentFirst"/>
        </xsl:when>
        <xsl:when test="ft:contentBefore">
            <xsl:apply-templates select="ft:contentBefore"/>
        </xsl:when>
    </xsl:choose>
</xsl:template>

<xsl:template name="contentAfter">
    <xsl:choose>
        <xsl:when test="ft:contentLast and not(following-sibling::ft:property[2] or following-sibling::ft:value[2])">
            <xsl:apply-templates select="ft:contentLast"/>
        </xsl:when>
        <xsl:when test="ft:contentAfter">
            <xsl:apply-templates select="ft:contentAfter"/>
        </xsl:when>
    </xsl:choose>
</xsl:template>

<xsl:template name="contentNoValue">
    <xsl:if test="not(ft:value)">
        <xsl:apply-templates select="ft:contentNoValue"/>
    </xsl:if>
</xsl:template>

<xsl:template match="ft:contentAfter|ft:contentLast|ft:contentBefore|ft:contentFirst">
    <xsl:copy-of select="child::node()"/>
</xsl:template>

<xsl:template match="ft:contentNoValue">
    <xsl:copy-of select="child::node()"/>
</xsl:template>

</xsl:stylesheet>
