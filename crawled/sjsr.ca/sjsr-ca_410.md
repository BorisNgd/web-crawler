---
url: https://sjsr.ca/wp-content/plugins/accessible-links/js/accessible-links.js?ver=6.9.4
title: sjsr.ca
date_crawled: '2026-03-25T01:47:42Z'
source_domain: sjsr.ca
depth: 2
parent_url: https://sjsr.ca/communiques/recherche-de-victimes-potentielles-de-miguel-theriault/
word_count: 54
rendering_mode: static
---

/* Edmond Pelletier */
/* Script pour auto-générer les addendas de lien sur le site */
jQuery(document).ready(function($) {
jQuery("div.fl-content a[target!='_blank']").each(function(i,obj){ jQuery(this).append("Ouvre le lien dans une nouvelle page")});
//jQuery("div.fl-content .fl-module:not('.cacheicone') * a[target='_blank']").each(function(i,obj){ jQuery(this).append("Ouvre le lien dans une nouvelle fenêtre ")});
// 2019
jQuery("div.fl-col-content.fl-node-content .fl-module:not('.cacheicone') * a[target='_blank']").each(function(i,obj){ jQuery(this).append("Ouvre le lien dans une nouvelle fenêtre ")});
})
