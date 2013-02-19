<?xml version="1.0" encoding="UTF-8"?>

<!-- Sorts a fresnel result tree -->

<xsl:stylesheet
    version = "1.0"
    xmlns:xsl   = "http://www.w3.org/1999/XSL/Transform"
    xmlns       = "http://www.andonyar.com/rec/2012/sempipe/fresnelxml"
    exclude-result-prefixes="xsl"
>

<xsl:output
     method="xml"
     encoding="UTF-8"
     indent="yes" />

<!-- Identity transformation -->

<xsl:template match="@*|node()">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

</xsl:stylesheet>
