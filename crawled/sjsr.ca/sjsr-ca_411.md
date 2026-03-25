---
url: https://sjsr.ca/wp-content/themes/sjsr/style.css?ver=6.9.4
title: sjsr.ca
date_crawled: '2026-03-25T01:47:42Z'
source_domain: sjsr.ca
depth: 2
parent_url: https://sjsr.ca/communiques/recherche-de-victimes-potentielles-de-miguel-theriault/
word_count: 937
rendering_mode: static
---

/*
Theme Name: Ville de Saint-Jean-sur-Richelieu
Theme URI: https://www.sjsr.ca
Version: 1.0
Description: Thème personnalisé pour la Ville de Saint-Jean-sur-Richelieu utilisant [Beaver Builder](https://www.wpbeaverbuilder.com/) et les frameworks [Bootstrap](https://getbootstrap.com/) et [Fontawesome](https://fontawesome.com/).
Author: S2B Solution
Author URI: https://www.s2bsolution.com
template: bb-theme
*/
/* Palette de couleurs
* Blanc : #fff
* Gris pale : #efefef
* Gris : #707070
* Bourgogne : #b2334e
* Bleu : #005983
* Aqua : #00dbed
* Noir : #000
*/
.fullwidthbanner-container, [id^="rev_slider_"] {
overflow: visible !important;
display: block !important;
}
.rs-parallax-wrap span[id^="slider-"] img {
width: 100%;
}
/* HEADER */
/* Top Nav */
.fl-page-bar {
border-bottom: none;
}
.fl-page-bar {
padding-top: 35px;
}
/* Nav accessibilité*/
.menu-a11y {
font-size: 18px;
}
.menu-a11y .fa-adjust {
padding-left: 10px;
}
.menu-a11y ul li {
line-height: 22px !important;
}
.menu-a11y ul li:nth-child(4) {
margin-top: 16px;
}
.ubermenu .ubermenu-item:not(.menu-accessible) + .menu-accessible {
margin-top: 15px;
}
.menu-accessible > a.nav-link {
padding-top: 0;
padding-bottom: 0;
}
.menu-accessible > a.nav-link > span {
font-size: 14px;
line-height: normal;
}
/* Font increase */
.medium {
font-size: 115%;
}
.largest {
font-size: 130%;
}
/* Navigation */
.fl-page-nav-right .fl-page-header-wrap {
border-bottom: none;
}
/* Navigation - bold du 1er niveau */
ul#menu-menu-principal-1>li>ul>li a {
font-weight: bold !important;
}
ul#menu-menu-principal-1>li>ul>li ul a {
font-weight: normal !important;
}
/* GENERAL */
/* Rendre liens dans les textes plus visibles */
.fl-content p a {
font-weight: bold;
}
.fl-builder-content a {
font-weight: bold;
}
/* Barre de Notifications */
.pum-content a {
color: #fff;
}
/* Module Feed BB - Read more */
.fl-post-feed .fl-post-feed-more {
margin-top: 0;
}
/* Accordéons */
.fl-accordion .fl-accordion-button {
font-weight: 700;
}
/* Titres */
.fl-module-heading h2.fl-heading,
.fl-module-heading h3.fl-heading {
margin-top: 1em !important;
}
/* Ajustement PowerPack Table */
.tablesaw td {
line-height: 1.5em;
}
/* Encadrés 2 colonnes intégrés dans des accordéons */
.encadre-2col-sjsr {
border: 1px solid #ccc;
background-color: #ededed;
overflow: hidden;
}
.encadre-2col-sjsr div {
padding: 20px;
}
#encadre-2col-sjsr-gauche {
float: left;
width: auto;
}
#encadre-2col-sjsr-droite {
overflow: hidden;
}
/* Espacement des LI */
li {
margin-bottom: 0.5em
}
/* ACCUEIL */
/* Recherche centrée */
.widget_search form {
width: 352px;
margin: 0 auto;
}
.widget_search form .fl-search-input {
background-color: transparent;
color: #fff;
font-size: 20px;
text-transform: uppercase;
}
/* Recherche */
.search-form {
border: 1px solid #fff;
}
.search-form .search-field::placeholder {
color: #fff;
text-transform: uppercase;
opacity: 0.95;
}
.search-form .search-field,
.search-form .search-field:focus,
.search-form .search-field:focus-within {
background-color: inherit;
border: none;
width: 300px;
color: #fff;
font-size: 24px;
font-weight: 400;
}
.search-form .search-submit {
background-color: inherit;
border: none;
padding: 15px;
}
.search-form .search-submit:hover {
background-color: rgba(255, 255, 255, 0.2);
}
/**
* Ajustements à la Recherche pour browsers Microsoft
* @url https://base16solutions.wordpress.com/2018/03/12/css-hacks-to-target-latest-ie-11-and-edge-versions/
*/
/* Microsoft Edge Browser 12+ (All) - @supports method */
@media all and (-ms-high-contrast: none), (-ms-high-contrast: active) {
.search-form label {
height: 26px;
}
.search-form .search-submit {
background-color: transparent !important;
}
.search-form .search-field:-ms-input-placeholder {
color: #fff !important;
text-transform: uppercase !important;
opacity: 0.95;
}
.search-form input[type=search] {
background-color: transparent !important;
border: none !important;
width: 300px !important;
color: #fff !important;
font-size: 24px;
font-weight: 400;
}
}
/* Microsoft Edge Browser 15+ - @supports method */
@supports (-ms-ime-align:auto) and (-webkit-text-stroke:initial) {
.search-form .search-submit {
background-color: transparent !important;
}
.search-form .search-field::-ms-input-placeholder {
color: #fff !important;
text-transform: uppercase !important;
opacity: 0.95;
}
.search-form input[type=search] {
background-color: transparent !important;
border: none !important;
width: 300px !important;
color: #fff !important;
font-size: 24px;
font-weight: 400;
}
}
/* Section bleue */
.accueil-section {
position: relative;
}
.accueil-section:after {
content: '';
height: 70%;
width: 1px;
position: absolute;
right: 0;
top: 15%;
background-color: #fff;
}
.fl-col-content>.section-bloc {
border-bottom: 10px solid #005983;
}
.fl-col-content>.section-bloc:hover {
border-bottom: 10px solid #fff;
}
/* Sélecteur de destinations */
.destinations {
text-align: center;
}
#sjsr-destination div {
display: inline;
padding: 0 15px;
}
select#sjsr-action,
select#sjsr-endroit {
background-color: #efefee;
padding: 4px 18px;
}
.destinations a {
color: #111;
}
/* Dans l'actualité */
.home .fl-post-feed-header {
margin-bottom: 0;
}
.home .fl-post-feed-more {
margin-top: 0;
}
/* Article */
.fl-photo-caption {
overflow: visible;
white-space: inherit;
text-align: left;
}
/* FOOTER */
/* Enlever bordures */
footer {
margin-top: 4em;
}
.fl-page-footer-widgets {
border-top: none;
}
.fl-page-footer {
border-top: none;
}
/* Widget de newsletter */
.fl-page-footer-widgets .col-sm-4:nth-child(2) {
padding-right: 40px !important;
}
.fl-page-footer-widgets-row .gform_wrapper .gform_footer input[type="submit"] {
background-color: transparent;
float: right;
}
.gform_wrapper .gform_footer {
padding: 0 0 5px 0 !important;
}
/* Widget de messages */
.fl-page-footer-widgets .col-sm-4:nth-child(2) .fl-widget:nth-child(2) {
padding-top: 20px;
}
a.footer-link {
font-family: "Open Sans", sans-serif;
color: #b2334e;
padding-right: 28px;
}
/* Widget des medias sociaux */
.fl-page-footer-widgets-row .col-sm-4:last-child {
text-align: left;
background-color: #005983;
height: 0;
padding: 0;
}
.fl-page-footer-widgets-row #custom_html-7 h4 {
color: #fff;
padding-right: 20px;
}
.fl-page-footer-widgets-row .custom-html-widget a i.fab {
color: #fff;
font-size: 2em;
padding-right: 20px;
}
/* Copyright */
.mention,
.mention a {
color: #919191;
}
/* FORMS */
/* Gravity Forms - Pages */
.gform_wrapper .gform_next_button,
.gform_wrapper .gform_previous_button,
.gform_wrapper .gform_button {
transition: all 0.5s ease;
background-color: #b2334e !important;
color: #fff !important;
padding: 8px 14px 10px;
}
.gform_wrapper .gform_next_button:hover,
.gform_wrapper .gform_previous_button:hover,
.gform_wrapper .gform_button:hover {
background-color: #005983 !important;
}
/* MOBILE */
@media (min-width: 992px) {
.fl-page-footer-container {
padding-top: 60px;
padding-bottom: 50px
}
}
/* Modifie la taille des titres sur mobile */
@media only screen and (max-width: 767px) {
.fl-page-bar {
display: none;
}
.titre-page-sjsr h1 {
font-size: 28px;
line-height: 1.3;
}
}
/* Retire les alignements problématiques sur mobile */
@media only screen and (max-width: 767px) {
.wp-caption.alignright {
float: none;
margin: 0 0 0 0;
}
.wp-caption.alignleft {
float: none;
margin: 0 0 0 0;
}
a img.alignleft {
float: none;
margin: 0 10 0 0;
width: 100%;
}
}
@media screen and (max-width: 400px) {
#encadre-2col-sjsr-gauche {
float: none;
width: auto;
border: 0;
}
}
