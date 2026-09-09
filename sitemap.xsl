<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:sitemap="http://www.sitemaps.org/schemas/sitemap/0.9"
                exclude-result-prefixes="sitemap">

  <xsl:output method="html" indent="yes" encoding="UTF-8" doctype-system="about:legacy-compat" />

  <xsl:template match="/">
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="color-scheme" content="dark" />
        <meta name="robots" content="noindex" />
        <title>Sitemap · sciBASIC# — VisualBasic for Scientific Computing</title>
        <style>
* { box-sizing: border-box; }
html { background: #030303; }
body {
  margin: 0;
  padding: 0 0 48px 0;
  background: #030303;
  color: #f2f2f2;
  font-family: Inter, "Helvetica Neue", "Segoe UI", system-ui, sans-serif;
  font-size: 15px;
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}
a { color: #9a9a9a; text-decoration: none; }
a:hover { text-decoration: underline; }
.wrap { max-width: 1120px; margin: 0 auto; padding: 40px 20px 0 20px; }
.head { padding-bottom: 22px; border-bottom: 1px solid #183f1c; margin-bottom: 24px; }
.kicker {
  display: inline-block;
  font-size: 11px;
  letter-spacing: 0.18em;
  font-weight: 600;
  color: #1a1a1a;
  background: #3fae4a;
  padding: 3px 9px;
  border-radius: 999px;
}
h1 { font-size: 30px; line-height: 1.2; margin: 14px 0 6px 0; font-weight: 600; color: #f2f2f2; }
.sub { margin: 0 0 10px 0; color: #9a9a9a; }
.meta { margin: 0; color: #9a9a9a; font-size: 13px; }
.meta b { color: #f2f2f2; }
.dot { margin: 0 8px; opacity: 0.6; }
.card {
  background: #151515;
  border: 1px solid #2b2b2b;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 0 rgba(255,255,255,0.03), 0 12px 32px rgba(0,0,0,0.55);
}
table.sitemap { width: 100%; border-collapse: collapse; font-size: 14px; }
table.sitemap th {
  text-align: left;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #9a9a9a;
  font-weight: 600;
  padding: 12px 14px;
  background: #1e3721;
  border-bottom: 1px solid #2b2b2b;
  white-space: nowrap;
}
table.sitemap td { padding: 10px 14px; border-bottom: 1px solid #2b2b2b; vertical-align: middle; }
table.sitemap tbody tr:nth-child(even) { background: #0d0d0d; }
table.sitemap tbody tr:hover { background: #1d311f; }
table.sitemap tbody tr:last-child td { border-bottom: none; }
td.num, th.num { width: 58px; color: #9a9a9a; font-variant-numeric: tabular-nums; }
td.loc { word-break: break-all; }
td.loc a { font-weight: 500; }
td.time, th.time { width: 130px; color: #9a9a9a; white-space: nowrap; }
td.freq, th.freq { width: 120px; }
td.prio, th.prio { width: 150px; }
.tag {
  display: inline-block;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  color: #9a9a9a;
  background: #1e3721;
  border: 1px solid #2b2b2b;
}
.bar {
  display: inline-block;
  width: 76px;
  height: 6px;
  border-radius: 999px;
  background: #1e3721;
  overflow: hidden;
  vertical-align: middle;
  margin-right: 8px;
}
.bar i { display: block; height: 100%; background: #3fae4a; border-radius: 999px; }
.val { color: #9a9a9a; font-variant-numeric: tabular-nums; font-size: 13px; }
.empty { color: #9a9a9a; padding: 24px 0; }
.foot { margin-top: 20px; color: #9a9a9a; font-size: 12px; }
.foot b { color: #3fae4a; font-weight: 600; }
@media (max-width: 720px) {
  .wrap { padding: 24px 12px 0 12px; }
  h1 { font-size: 24px; }
  table.sitemap th, table.sitemap td { padding: 8px 10px; }
}
        </style>
      </head>
      <body>
        <div class="wrap">
          <header class="head">
            <div class="kicker">SITEMAP</div>
            <h1>sciBASIC# — VisualBasic for Scientific Computing</h1>
            <p class="sub">
              <a class="home" href="https://scibasic.net/">https://scibasic.net/</a>
            </p>
            <p class="meta">
              <span class="stat"><b><xsl:value-of select="count(sitemap:urlset/sitemap:url)" /></b> urls</span>
              <span class="dot">·</span>
              <span class="stat">generated at 2026-09-09 09:17</span>
            </p>
          </header>

          <xsl:choose>
            <xsl:when test="count(sitemap:urlset/sitemap:url) = 0">
              <p class="empty">There is no url entry inside this sitemap document.</p>
            </xsl:when>
            <xsl:otherwise>
              <div class="card">
                <table class="sitemap">
                  <thead>
                    <tr>
                      <th class="num">#</th>
                      <th class="loc">URL</th>
                      <th class="time">Last Modified</th>
                      <th class="freq">Frequency</th>
                      <th class="prio">Priority</th>
                    </tr>
                  </thead>
                  <tbody>
                    <xsl:for-each select="sitemap:urlset/sitemap:url">
                      <xsl:sort select="number(sitemap:priority)" order="descending" data-type="number" />
                      <xsl:sort select="sitemap:loc" order="ascending" data-type="text" />
                      <tr>
                        <td class="num"><xsl:value-of select="position()" /></td>
                        <td class="loc">
                          <a href="{sitemap:loc}"><xsl:value-of select="sitemap:loc" /></a>
                        </td>
                        <td class="time"><xsl:value-of select="sitemap:lastmod" /></td>
                        <td class="freq"><span class="tag"><xsl:value-of select="sitemap:changefreq" /></span></td>
                        <td class="prio">
                          <span class="bar">
                            <i>
                              <xsl:attribute name="style">
                                <xsl:text>width:</xsl:text>
                                <xsl:value-of select="round(number(sitemap:priority) * 100)" />
                                <xsl:text>%</xsl:text>
                              </xsl:attribute>
                            </i>
                          </span>
                          <span class="val"><xsl:value-of select="sitemap:priority" /></span>
                        </td>
                      </tr>
                    </xsl:for-each>
                  </tbody>
                </table>
              </div>
            </xsl:otherwise>
          </xsl:choose>

          <footer class="foot">
            <span>Generated by <b>GCModeller Sitemap</b> · sitemap protocol 0.9</span>
          </footer>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
