<?xml version="1.0" encoding="UTF-8"?>

<!-- The HTML serilaization of HTML 5 has some annoying differencies
from the XHTML one:

- No XML parsing instructions allowed
- Consequently, the charset has to be indicated in a meta element
- A meaningless doctype declaration ensures that browsers don't go
  into quirks mode
- Namespaces do not exist, namespace declarations are invalid

Important: Is this XSLT used through libxml, then some changes have no
effect, because in this case serialization is not under the control of
libxslt. This is especially a problem with the 
 -->

<xsl:stylesheet
    version = "1.0"
    xmlns:xsl   = "http://www.w3.org/1999/XSL/Transform"
    xmlns:fn    = "http://www.w3.org/2005/xpath-functions"
    xmlns:html  = "http://www.w3.org/1999/xhtml"
    xmlns       = "http://www.w3.org/1999/xhtml"
    exclude-result-prefixes="xsl fn"
>

<xsl:output
     method="xml"
     omit-xml-declaration="yes"
     doctype-system="about:legacy-compat"
     encoding="UTF-8"
     indent="yes" />

<xsl:template match="html:head">
  <xsl:copy>
    <meta charset="utf-8"/>
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
