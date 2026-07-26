window.StarletteAdmin = window.StarletteAdmin || {};

// Clones the root element of `<template data-sa-template="name">` found
// anywhere in the document. Returns null if no such template exists, so a
// theme fragment that omits a template disables the feature instead of
// throwing.
StarletteAdmin.template = function (name) {
  var tpl = document.querySelector('template[data-sa-template="' + name + '"]');
  if (!tpl || !tpl.content.firstElementChild) return null;
  return tpl.content.firstElementChild.cloneNode(true);
};

// Adds one or more space-separated classes to el, since a role may resolve
// to several tokens.
StarletteAdmin.addClass = function (el, value) {
  if (!el || !value) return;
  String(value)
    .split(/\s+/)
    .filter(Boolean)
    .forEach(function (c) {
      el.classList.add(c);
    });
};

// Removes one or more space-separated classes from el, the addClass mirror.
StarletteAdmin.removeClass = function (el, value) {
  if (!el || !value) return;
  String(value)
    .split(/\s+/)
    .filter(Boolean)
    .forEach(function (c) {
      el.classList.remove(c);
    });
};

// Runs fn(node) on el's descendant carrying `data-sa-slot="name"`; a no-op
// when the slot is absent, so a theme's fragment may drop a slot it does
// not want.
StarletteAdmin.fillSlot = function (el, name, fn) {
  var node = el && el.querySelector('[data-sa-slot="' + name + '"]');
  if (node) fn(node);
};
