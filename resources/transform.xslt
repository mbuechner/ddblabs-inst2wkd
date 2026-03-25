<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:org="http://www.deutsche-digitale-bibliothek.de/ns/organization"
  exclude-result-prefixes="xsl">

  <xsl:output method="xml" indent="yes" encoding="UTF-8"/>

  <xsl:template match="/intermediate">
    <org:organization>
      <org:created><xsl:value-of select="created"/></org:created>
      <org:creatorId><xsl:value-of select="creatorId"/></org:creatorId>
      <org:modified><xsl:value-of select="modified"/></org:modified>
      <org:modifierId><xsl:value-of select="modifierId"/></org:modifierId>
      <org:status><xsl:value-of select="status"/></org:status>
      <org:recordType><xsl:value-of select="recordType"/></org:recordType>
      <org:id><xsl:value-of select="id"/></org:id>
      <org:wkdId><xsl:value-of select="wkdId"/></org:wkdId>

      <xsl:if test="string(orgParent)">
        <org:orgParent><xsl:value-of select="orgParent"/></org:orgParent>
      </xsl:if>

      <xsl:if test="string(pid)">
        <org:pid><xsl:value-of select="pid"/></org:pid>
      </xsl:if>

      <xsl:if test="string(authorityId)">
        <org:authorityId><xsl:value-of select="authorityId"/></org:authorityId>
      </xsl:if>

      <xsl:for-each select="displayNames/displayName">
        <org:displayName lang="{ @lang }"><xsl:value-of select="."/></org:displayName>
      </xsl:for-each>

      <xsl:for-each select="abbreviations/abbreviation">
        <org:abbreviation lang="{ @lang }"><xsl:value-of select="."/></org:abbreviation>
      </xsl:for-each>

      <org:sector><xsl:value-of select="sector"/></org:sector>
      <xsl:if test="string(subsector)">
        <org:subsector><xsl:value-of select="subsector"/></org:subsector>
      </xsl:if>

      <xsl:for-each select="descriptions/description">
        <org:description lang="{ @lang }"><xsl:value-of select="."/></org:description>
      </xsl:for-each>

      <xsl:if test="string(fundingAgency)">
        <org:fundingAgency><xsl:value-of select="fundingAgency"/></org:fundingAgency>
      </xsl:if>

      <xsl:if test="string(legalStatus)">
        <org:legalStatus><xsl:value-of select="legalStatus"/></org:legalStatus>
      </xsl:if>

      <org:address>
        <xsl:if test="string(address/street)">
          <org:street><xsl:value-of select="address/street"/></org:street>
        </xsl:if>

        <xsl:if test="string(address/houseIdentifier)">
          <org:houseIdentifier><xsl:value-of select="address/houseIdentifier"/></org:houseIdentifier>
        </xsl:if>

        <xsl:if test="string(address/addressSupplement)">
          <org:addressSupplement><xsl:value-of select="address/addressSupplement"/></org:addressSupplement>
        </xsl:if>

        <xsl:if test="string(address/postalCode)">
          <org:postalCode><xsl:value-of select="address/postalCode"/></org:postalCode>
        </xsl:if>

        <org:city uri="{ address/city/@uri }">
          <xsl:for-each select="address/city/label">
            <org:label lang="{ @lang }"><xsl:value-of select="."/></org:label>
          </xsl:for-each>
        </org:city>

        <xsl:if test="address/state">
          <org:state uri="{ address/state/@uri }">
            <xsl:for-each select="address/state/label">
              <org:label lang="{ @lang }"><xsl:value-of select="."/></org:label>
            </xsl:for-each>
          </org:state>
        </xsl:if>

        <org:country uri="{ address/country/@uri }">
          <xsl:for-each select="address/country/label">
            <org:label lang="{ @lang }"><xsl:value-of select="."/></org:label>
          </xsl:for-each>
        </org:country>

        <xsl:if test="address/coordinates">
          <org:coordinates>
            <org:latitude><xsl:value-of select="address/coordinates/latitude"/></org:latitude>
            <org:longitude><xsl:value-of select="address/coordinates/longitude"/></org:longitude>
          </org:coordinates>
        </xsl:if>

        <xsl:if test="string(address/locationDisplayName)">
          <org:locationDisplayName><xsl:value-of select="address/locationDisplayName"/></org:locationDisplayName>
        </xsl:if>
      </org:address>

      <xsl:if test="string(email)">
        <org:email><xsl:value-of select="email"/></org:email>
      </xsl:if>

      <xsl:if test="string(url)">
        <org:url><xsl:value-of select="url"/></org:url>
      </xsl:if>

      <xsl:if test="string(logo)">
        <org:logo><xsl:value-of select="logo"/></org:logo>
      </xsl:if>

      <xsl:if test="string(telephone)">
        <org:telephone><xsl:value-of select="telephone"/></org:telephone>
      </xsl:if>

      <xsl:if test="string(fax)">
        <org:fax><xsl:value-of select="fax"/></org:fax>
      </xsl:if>

      <xsl:if test="string(facebook)">
        <org:facebook><xsl:value-of select="facebook"/></org:facebook>
      </xsl:if>

      <xsl:if test="string(twitter)">
        <org:twitter><xsl:value-of select="twitter"/></org:twitter>
      </xsl:if>

      <xsl:if test="string(instagram)">
        <org:instagram><xsl:value-of select="instagram"/></org:instagram>
      </xsl:if>

      <xsl:if test="string(bookmarkListId)">
        <org:bookmarkListId><xsl:value-of select="bookmarkListId"/></org:bookmarkListId>
      </xsl:if>
    </org:organization>
  </xsl:template>

</xsl:stylesheet>
