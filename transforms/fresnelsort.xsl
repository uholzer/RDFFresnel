<?xml version="1.0" encoding="UTF-8"?>

<!-- Sorts a fresnel result tree -->

<xsl:stylesheet
    version = "1.0"
    xmlns:xsl   = "http://www.w3.org/1999/XSL/Transform"
    xmlns:fn    = "http://www.w3.org/2005/xpath-functions"
    xmlns:fres  = "http://www.andonyar.com/rec/2012/sempipe/fresnelxml"
    xmlns       = "http://www.andonyar.com/rec/2012/sempipe/fresnelxml"
    exclude-result-prefixes="fn"
>


<xsl:template match="/">
    <xsl:apply-templates select="@*|node()"/>
</xsl:template>

<xsl:template match="fres:property"><!-- fres:property[contains(fres:format,'sort:canonical')] -->
    <xsl:copy>
        <xsl:apply-templates select="@*"/>
        <xsl:apply-templates select="fres:value[@type='resource']">
            <xsl:sort select="fres:resource/@uri"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="fres:value[not(@type='resource')]">
            <xsl:sort select="fres:literal"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="node()[not(self::fres:value)]"/>
    </xsl:copy>
</xsl:template>

<!-- Identity transformation -->

<xsl:template match="@*|node()">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

</xsl:stylesheet>
