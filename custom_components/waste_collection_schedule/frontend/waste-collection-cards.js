/* Generated from frontend/src by `npm run build`. Do not edit by hand. */
// node_modules/@lit/reactive-element/css-tag.js
var e = globalThis, t = e.ShadowRoot && (e.ShadyCSS === void 0 || e.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, n = Symbol(), r = /* @__PURE__ */ new WeakMap(), i = class {
	constructor(e, t, r) {
		if (this._$cssResult$ = !0, r !== n) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
		this.cssText = e, this.t = t;
	}
	get styleSheet() {
		let e = this.o, n = this.t;
		if (t && e === void 0) {
			let t = n !== void 0 && n.length === 1;
			t && (e = r.get(n)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), t && r.set(n, e));
		}
		return e;
	}
	toString() {
		return this.cssText;
	}
}, a = (e) => new i(typeof e == "string" ? e : e + "", void 0, n), o = (e, ...t) => new i(e.length === 1 ? e[0] : t.reduce((t, n, r) => t + ((e) => {
	if (!0 === e._$cssResult$) return e.cssText;
	if (typeof e == "number") return e;
	throw Error("Value passed to 'css' function must be a 'css' function result: " + e + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
})(n) + e[r + 1], e[0]), e, n), s = (n, r) => {
	if (t) n.adoptedStyleSheets = r.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
	else for (let t of r) {
		let r = document.createElement("style"), i = e.litNonce;
		i !== void 0 && r.setAttribute("nonce", i), r.textContent = t.cssText, n.appendChild(r);
	}
}, c = t ? (e) => e : (e) => e instanceof CSSStyleSheet ? ((e) => {
	let t = "";
	for (let n of e.cssRules) t += n.cssText;
	return a(t);
})(e) : e, { is: l, defineProperty: u, getOwnPropertyDescriptor: d, getOwnPropertyNames: f, getOwnPropertySymbols: p, getPrototypeOf: m } = Object, h = globalThis, ee = h.trustedTypes, te = ee ? ee.emptyScript : "", ne = h.reactiveElementPolyfillSupport, g = (e, t) => e, _ = {
	toAttribute(e, t) {
		switch (t) {
			case Boolean:
				e = e ? te : null;
				break;
			case Object:
			case Array: e = e == null ? e : JSON.stringify(e);
		}
		return e;
	},
	fromAttribute(e, t) {
		let n = e;
		switch (t) {
			case Boolean:
				n = e !== null;
				break;
			case Number:
				n = e === null ? null : Number(e);
				break;
			case Object:
			case Array: try {
				n = JSON.parse(e);
			} catch {
				n = null;
			}
		}
		return n;
	}
}, re = (e, t) => !l(e, t), ie = {
	attribute: !0,
	type: String,
	converter: _,
	reflect: !1,
	useDefault: !1,
	hasChanged: re
};
Symbol.metadata ??= Symbol("metadata"), h.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var v = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = ie) {
		if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
			let n = Symbol(), r = this.getPropertyDescriptor(e, n, t);
			r !== void 0 && u(this.prototype, e, r);
		}
	}
	static getPropertyDescriptor(e, t, n) {
		let { get: r, set: i } = d(this.prototype, e) ?? {
			get() {
				return this[t];
			},
			set(e) {
				this[t] = e;
			}
		};
		return {
			get: r,
			set(t) {
				let a = r?.call(this);
				i?.call(this, t), this.requestUpdate(e, a, n);
			},
			configurable: !0,
			enumerable: !0
		};
	}
	static getPropertyOptions(e) {
		return this.elementProperties.get(e) ?? ie;
	}
	static _$Ei() {
		if (this.hasOwnProperty(g("elementProperties"))) return;
		let e = m(this);
		e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(g("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(g("properties"))) {
			let e = this.properties, t = [...f(e), ...p(e)];
			for (let n of t) this.createProperty(n, e[n]);
		}
		let e = this[Symbol.metadata];
		if (e !== null) {
			let t = litPropertyMetadata.get(e);
			if (t !== void 0) for (let [e, n] of t) this.elementProperties.set(e, n);
		}
		this._$Eh = /* @__PURE__ */ new Map();
		for (let [e, t] of this.elementProperties) {
			let n = this._$Eu(e, t);
			n !== void 0 && this._$Eh.set(n, e);
		}
		this.elementStyles = this.finalizeStyles(this.styles);
	}
	static finalizeStyles(e) {
		let t = [];
		if (Array.isArray(e)) {
			let n = new Set(e.flat(1 / 0).reverse());
			for (let e of n) t.unshift(c(e));
		} else e !== void 0 && t.push(c(e));
		return t;
	}
	static _$Eu(e, t) {
		let n = t.attribute;
		return !1 === n ? void 0 : typeof n == "string" ? n : typeof e == "string" ? e.toLowerCase() : void 0;
	}
	constructor() {
		super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
	}
	_$Ev() {
		this._$ES = new Promise((e) => this.enableUpdating = e), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((e) => e(this));
	}
	addController(e) {
		(this._$EO ??= /* @__PURE__ */ new Set()).add(e), this.renderRoot !== void 0 && this.isConnected && e.hostConnected?.();
	}
	removeController(e) {
		this._$EO?.delete(e);
	}
	_$E_() {
		let e = /* @__PURE__ */ new Map(), t = this.constructor.elementProperties;
		for (let n of t.keys()) this.hasOwnProperty(n) && (e.set(n, this[n]), delete this[n]);
		e.size > 0 && (this._$Ep = e);
	}
	createRenderRoot() {
		let e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
		return s(e, this.constructor.elementStyles), e;
	}
	connectedCallback() {
		this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((e) => e.hostConnected?.());
	}
	enableUpdating(e) {}
	disconnectedCallback() {
		this._$EO?.forEach((e) => e.hostDisconnected?.());
	}
	attributeChangedCallback(e, t, n) {
		this._$AK(e, n);
	}
	_$ET(e, t) {
		let n = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, n);
		if (r !== void 0 && !0 === n.reflect) {
			let i = (n.converter?.toAttribute === void 0 ? _ : n.converter).toAttribute(t, n.type);
			this._$Em = e, i == null ? this.removeAttribute(r) : this.setAttribute(r, i), this._$Em = null;
		}
	}
	_$AK(e, t) {
		let n = this.constructor, r = n._$Eh.get(e);
		if (r !== void 0 && this._$Em !== r) {
			let e = n.getPropertyOptions(r), i = typeof e.converter == "function" ? { fromAttribute: e.converter } : e.converter?.fromAttribute === void 0 ? _ : e.converter;
			this._$Em = r;
			let a = i.fromAttribute(t, e.type);
			this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
		}
	}
	requestUpdate(e, t, n, r = !1, i) {
		if (e !== void 0) {
			let a = this.constructor;
			if (!1 === r && (i = this[e]), n ??= a.getPropertyOptions(e), !((n.hasChanged ?? re)(i, t) || n.useDefault && n.reflect && i === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, n)))) return;
			this.C(e, t, n);
		}
		!1 === this.isUpdatePending && (this._$ES = this._$EP());
	}
	C(e, t, { useDefault: n, reflect: r, wrapped: i }, a) {
		n && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, a ?? t ?? this[e]), !0 !== i || a !== void 0) || (this._$AL.has(e) || (this.hasUpdated || n || (t = void 0), this._$AL.set(e, t)), !0 === r && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
	}
	async _$EP() {
		this.isUpdatePending = !0;
		try {
			await this._$ES;
		} catch (e) {
			Promise.reject(e);
		}
		let e = this.scheduleUpdate();
		return e != null && await e, !this.isUpdatePending;
	}
	scheduleUpdate() {
		return this.performUpdate();
	}
	performUpdate() {
		if (!this.isUpdatePending) return;
		if (!this.hasUpdated) {
			if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
				for (let [e, t] of this._$Ep) this[e] = t;
				this._$Ep = void 0;
			}
			let e = this.constructor.elementProperties;
			if (e.size > 0) for (let [t, n] of e) {
				let { wrapped: e } = n, r = this[t];
				!0 !== e || this._$AL.has(t) || r === void 0 || this.C(t, void 0, n, r);
			}
		}
		let e = !1, t = this._$AL;
		try {
			e = this.shouldUpdate(t), e ? (this.willUpdate(t), this._$EO?.forEach((e) => e.hostUpdate?.()), this.update(t)) : this._$EM();
		} catch (t) {
			throw e = !1, this._$EM(), t;
		}
		e && this._$AE(t);
	}
	willUpdate(e) {}
	_$AE(e) {
		this._$EO?.forEach((e) => e.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
	}
	_$EM() {
		this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
	}
	get updateComplete() {
		return this.getUpdateComplete();
	}
	getUpdateComplete() {
		return this._$ES;
	}
	shouldUpdate(e) {
		return !0;
	}
	update(e) {
		this._$Eq &&= this._$Eq.forEach((e) => this._$ET(e, this[e])), this._$EM();
	}
	updated(e) {}
	firstUpdated(e) {}
};
v.elementStyles = [], v.shadowRootOptions = { mode: "open" }, v[g("elementProperties")] = /* @__PURE__ */ new Map(), v[g("finalized")] = /* @__PURE__ */ new Map(), ne?.({ ReactiveElement: v }), (h.reactiveElementVersions ??= []).push("2.1.2");
// node_modules/lit-html/lit-html.js
var y = globalThis, ae = (e) => e, b = y.trustedTypes, oe = b ? b.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, x = "$lit$", S = `lit$${Math.random().toFixed(9).slice(2)}$`, C = "?" + S, se = `<${C}>`, w = document, T = () => w.createComment(""), E = (e) => e === null || typeof e != "object" && typeof e != "function", D = Array.isArray, ce = (e) => D(e) || typeof e?.[Symbol.iterator] == "function", O = "[ 	\n\f\r]", k = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, le = /-->/g, ue = />/g, A = RegExp(`>|${O}(?:([^\\s"'>=/]+)(${O}*=${O}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), de = /'/g, fe = /"/g, pe = /^(?:script|style|textarea|title)$/i, j = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), M = Symbol.for("lit-noChange"), N = Symbol.for("lit-nothing"), me = /* @__PURE__ */ new WeakMap(), P = w.createTreeWalker(w, 129);
function he(e, t) {
	if (!D(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return oe === void 0 ? t : oe.createHTML(t);
}
var ge = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = k;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === k ? c[1] === "!--" ? o = le : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = A) : (pe.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = A) : o = ue : o === A ? c[0] === ">" ? (o = i ?? k, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? A : c[3] === "\"" ? fe : de) : o === fe || o === de ? o = A : o === le || o === ue ? o = k : (o = A, i = void 0);
		let d = o === A && e[t + 1].startsWith("/>") ? " " : "";
		a += o === k ? n + se : l >= 0 ? (r.push(s), n.slice(0, l) + x + n.slice(l) + S + d) : n + S + (l === -2 ? t : d);
	}
	return [he(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, F = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = ge(t, n);
		if (this.el = e.createElement(l, r), P.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = P.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(x)) {
					let t = u[o++], n = i.getAttribute(e).split(S), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? _e : r[1] === "?" ? ve : r[1] === "@" ? ye : z
					}), i.removeAttribute(e);
				} else e.startsWith(S) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (pe.test(i.tagName)) {
					let e = i.textContent.split(S), t = e.length - 1;
					if (t > 0) {
						i.textContent = b ? b.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], T()), P.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], T());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === C) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(S, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += S.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = w.createElement("template");
		return n.innerHTML = e, n;
	}
};
function I(e, t, n = e, r) {
	if (t === M) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = E(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = I(e, i._$AS(e, t.values), i, r)), t;
}
var L = class {
	constructor(e, t) {
		this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = t;
	}
	get parentNode() {
		return this._$AM.parentNode;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	u(e) {
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? w).importNode(t, !0);
		P.currentNode = r;
		let i = P.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new R(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new be(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = P.nextNode(), a++);
		}
		return P.currentNode = w, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, R = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = N, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
	}
	get parentNode() {
		let e = this._$AA.parentNode, t = this._$AM;
		return t !== void 0 && e?.nodeType === 11 && (e = t.parentNode), e;
	}
	get startNode() {
		return this._$AA;
	}
	get endNode() {
		return this._$AB;
	}
	_$AI(e, t = this) {
		e = I(this, e, t), E(e) ? e === N || e == null || e === "" ? (this._$AH !== N && this._$AR(), this._$AH = N) : e !== this._$AH && e !== M && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? ce(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== N && E(this._$AH) ? this._$AA.nextSibling.data = e : this.T(w.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = F.createElement(he(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new L(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = me.get(e.strings);
		return t === void 0 && me.set(e.strings, t = new F(e)), t;
	}
	k(t) {
		D(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(T()), this.O(T()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = ae(e).nextSibling;
			ae(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, z = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = N, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = N;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = I(this, e, t, 0), a = !E(e) || e !== this._$AH && e !== M, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = I(this, r[n + o], t, o), s === M && (s = this._$AH[o]), a ||= !E(s) || s !== this._$AH[o], s === N ? e = N : e !== N && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === N ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, _e = class extends z {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === N ? void 0 : e;
	}
}, ve = class extends z {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== N);
	}
}, ye = class extends z {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = I(this, e, t, 0) ?? N) === M) return;
		let n = this._$AH, r = e === N && n !== N || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== N && (n === N || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, be = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		I(this, e);
	}
}, xe = {
	M: x,
	P: S,
	A: C,
	C: 1,
	L: ge,
	R: L,
	D: ce,
	V: I,
	I: R,
	H: z,
	N: ve,
	U: ye,
	B: _e,
	F: be
}, Se = y.litHtmlPolyfillSupport;
Se?.(F, R), (y.litHtmlVersions ??= []).push("3.3.3");
var Ce = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new R(t.insertBefore(T(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, B = globalThis, V = class extends v {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Ce(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return M;
	}
};
V._$litElement$ = !0, V.finalized = !0, B.litElementHydrateSupport?.({ LitElement: V });
var we = B.litElementPolyfillSupport;
we?.({ LitElement: V }), (B.litElementVersions ??= []).push("4.2.2");
// node_modules/lit-html/directive.js
var Te = {
	ATTRIBUTE: 1,
	CHILD: 2,
	PROPERTY: 3,
	BOOLEAN_ATTRIBUTE: 4,
	EVENT: 5,
	ELEMENT: 6
}, H = (e) => (...t) => ({
	_$litDirective$: e,
	values: t
}), U = class {
	constructor(e) {}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AT(e, t, n) {
		this._$Ct = e, this._$AM = t, this._$Ci = n;
	}
	_$AS(e, t) {
		return this.update(e, t);
	}
	update(e, t) {
		return this.render(...t);
	}
}, Ee = "important", De = " !" + Ee, Oe = H(class extends U {
	constructor(e) {
		if (super(e), e.type !== Te.ATTRIBUTE || e.name !== "style" || e.strings?.length > 2) throw Error("The `styleMap` directive must be used in the `style` attribute and must be the only part in the attribute.");
	}
	render(e) {
		return Object.keys(e).reduce((t, n) => {
			let r = e[n];
			return r == null ? t : t + `${n = n.includes("-") ? n : n.replace(/(?:^(webkit|moz|ms|o)|)(?=[A-Z])/g, "-$&").toLowerCase()}:${r};`;
		}, "");
	}
	update(e, [t]) {
		let { style: n } = e.element;
		if (this.ft === void 0) return this.ft = new Set(Object.keys(t)), this.render(t);
		for (let e of this.ft) t[e] ?? (this.ft.delete(e), e.includes("-") ? n.removeProperty(e) : n[e] = null);
		for (let e in t) {
			let r = t[e];
			if (r != null) {
				this.ft.add(e);
				let t = typeof r == "string" && r.endsWith(De);
				e.includes("-") || t ? n.setProperty(e, t ? r.slice(0, -11) : r, t ? Ee : "") : n[e] = r;
			}
		}
		return M;
	}
}), { I: ke } = xe, Ae = (e) => e, je = () => document.createComment(""), W = (e, t, n) => {
	let r = e._$AA.parentNode, i = t === void 0 ? e._$AB : t._$AA;
	if (n === void 0) n = new ke(r.insertBefore(je(), i), r.insertBefore(je(), i), e, e.options);
	else {
		let t = n._$AB.nextSibling, a = n._$AM, o = a !== e;
		if (o) {
			let t;
			n._$AQ?.(e), n._$AM = e, n._$AP !== void 0 && (t = e._$AU) !== a._$AU && n._$AP(t);
		}
		if (t !== i || o) {
			let e = n._$AA;
			for (; e !== t;) {
				let t = Ae(e).nextSibling;
				Ae(r).insertBefore(e, i), e = t;
			}
		}
	}
	return n;
}, G = (e, t, n = e) => (e._$AI(t, n), e), Me = {}, Ne = (e, t = Me) => e._$AH = t, Pe = (e) => e._$AH, K = (e) => {
	e._$AR(), e._$AA.remove();
}, Fe = H(class extends U {
	constructor() {
		super(...arguments), this.key = N;
	}
	render(e, t) {
		return this.key = e, t;
	}
	update(e, [t, n]) {
		return t !== this.key && (Ne(e), this.key = t), n;
	}
}), Ie = (e, t, n) => {
	let r = /* @__PURE__ */ new Map();
	for (let i = t; i <= n; i++) r.set(e[i], i);
	return r;
}, Le = H(class extends U {
	constructor(e) {
		if (super(e), e.type !== Te.CHILD) throw Error("repeat() can only be used in text expressions");
	}
	dt(e, t, n) {
		let r;
		n === void 0 ? n = t : t !== void 0 && (r = t);
		let i = [], a = [], o = 0;
		for (let t of e) i[o] = r ? r(t, o) : o, a[o] = n(t, o), o++;
		return {
			values: a,
			keys: i
		};
	}
	render(e, t, n) {
		return this.dt(e, t, n).values;
	}
	update(e, [t, n, r]) {
		let i = Pe(e), { values: a, keys: o } = this.dt(t, n, r);
		if (!Array.isArray(i)) return this.ut = o, a;
		let s = this.ut ??= [], c = [], l, u, d = 0, f = i.length - 1, p = 0, m = a.length - 1;
		for (; d <= f && p <= m;) if (i[d] === null) d++;
		else if (i[f] === null) f--;
		else if (s[d] === o[p]) c[p] = G(i[d], a[p]), d++, p++;
		else if (s[f] === o[m]) c[m] = G(i[f], a[m]), f--, m--;
		else if (s[d] === o[m]) c[m] = G(i[d], a[m]), W(e, c[m + 1], i[d]), d++, m--;
		else if (s[f] === o[p]) c[p] = G(i[f], a[p]), W(e, i[d], i[f]), f--, p++;
		else if (l === void 0 && (l = Ie(o, p, m), u = Ie(s, d, f)), l.has(s[d])) {
			if (l.has(s[f])) {
				let t = u.get(o[p]), n = t === void 0 ? null : i[t];
				if (n === null) {
					let t = W(e, i[d]);
					G(t, a[p]), c[p] = t;
				} else c[p] = G(n, a[p]), W(e, i[d], n), i[t] = null;
				p++;
			} else K(i[f]), f--;
		} else K(i[d]), d++;
		for (; p <= m;) {
			let t = W(e, c[m + 1]);
			G(t, a[p]), c[p++] = t;
		}
		for (; d <= f;) {
			let e = i[d++];
			e !== null && K(e);
		}
		return this.ut = o, Ne(e, c), M;
	}
}), Re = o`
  :host {
    display: block;
    min-width: 0;
    height: 100%;
    font-family: var(--ha-font-family-body, inherit);
    font-size: var(--ha-font-size-m, 14px);
    --wcs-accent: var(--primary-color, #03a9f4);
  }
  .frame {
    container-type: inline-size;
    height: 100%;
    min-width: 0;
  }
  ha-card {
    height: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    color: var(--primary-text-color);
    overflow: hidden;
  }
  header {
    padding: var(--ha-space-5, 20px) var(--ha-space-5, 20px)
      var(--ha-space-3, 12px);
    display: flex;
    align-items: center;
    gap: var(--ha-space-3, 12px);
    flex: none;
  }
  header ha-icon {
    color: var(--wcs-accent);
  }
  h2 {
    margin: 0;
    font-family: var(--ha-font-family-heading, inherit);
    font-size: var(--ha-font-size-xl, var(--ha-card-header-font-size, 20px));
    line-height: 1.4;
    font-weight: var(--ha-font-weight-medium, 500);
    overflow-wrap: anywhere;
  }
  .content {
    padding: 0 var(--ha-space-4, 16px) var(--ha-space-4, 16px);
    overflow: auto;
    flex: 1;
    min-height: 0;
  }
  .state {
    padding: 16px 4px;
    color: var(--secondary-text-color);
    line-height: var(--ha-line-height-normal, 1.6);
    overflow-wrap: anywhere;
  }
  /* HA's default error red is below 4.5:1 on light cards: text stays in theme colours. */
  .error {
    display: flex;
    gap: var(--ha-space-3, 12px);
    align-items: flex-start;
    color: var(--primary-text-color);
  }
  .error > ha-icon {
    flex: none;
    color: var(--error-color);
  }
  .failed {
    color: var(--secondary-text-color);
    margin-bottom: 8px;
  }
  button {
    font: inherit;
    color: inherit;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
  }
  button:focus-visible {
    outline: 3px solid var(--primary-color);
    outline-offset: -3px;
  }
  .retry {
    background: none;
    border: 1px solid var(--divider-color);
    border-radius: var(--ha-border-radius-sm, 8px);
    min-height: 48px;
    padding: 0 16px;
  }
  .list {
    display: grid;
    gap: var(--ha-space-2, 8px);
  }
  .pickup {
    display: flex;
    align-items: center;
    gap: 14px;
    text-align: start;
    min-height: 72px;
    padding: var(--ha-space-3, 12px);
    border: 0;
    border-radius: var(--ha-border-radius-lg, 12px);
    background: var(--secondary-background-color);
    width: 100%;
    box-sizing: border-box;
  }
  .pickup:hover {
    background: var(--divider-color);
  }
  .visual {
    width: 48px;
    height: 48px;
    flex: none;
    display: grid;
    place-items: center;
    border-radius: 14px;
    background: var(--card-background-color);
    position: relative;
  }
  .visual:before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    border: 2px solid var(--divider-color);
    pointer-events: none;
  }
  /* Styled types get a tinted tile and a full-strength ring; name and date still carry the meaning. */
  .styled .visual {
    background: color-mix(
      in srgb,
      var(--bin-color) 16%,
      var(--card-background-color)
    );
  }
  .styled .visual:before {
    border-color: var(--bin-color);
  }
  [hidden] {
    display: none !important;
  }
  .visual ha-icon {
    --mdc-icon-size: 28px;
    color: var(--primary-text-color);
  }
  .visual img {
    height: 42px;
    width: 42px;
    object-fit: contain;
    border-radius: 10px;
  }
  .words {
    min-width: 0;
    flex: 1;
  }
  .name {
    font-weight: var(--ha-font-weight-medium, 500);
    line-height: 1.45;
    overflow-wrap: anywhere;
  }
  .meta {
    display: block;
    color: var(--secondary-text-color);
    font-size: var(--ha-font-size-m, 14px);
    line-height: 1.5;
    overflow-wrap: anywhere;
    margin-top: 3px;
  }
  .when {
    display: block;
    color: var(--primary-text-color);
    font-weight: var(--ha-font-weight-medium, 500);
    margin-top: 2px;
  }
  .hero .pickup {
    min-height: 108px;
  }
  .hero .name {
    font-size: var(--ha-font-size-l, 16px);
  }
  .hero .visual {
    width: 64px;
    height: 64px;
  }
  .hero .visual ha-icon {
    --mdc-icon-size: 36px;
  }
  .bins {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(130px, 100%), 1fr));
    gap: 10px;
  }
  .bins .pickup {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--ha-space-3, 12px);
    min-height: 170px;
  }
  .bins .words {
    width: 100%;
  }
  .bins .visual {
    width: 56px;
    height: 56px;
  }
  .day {
    font-size: var(--ha-font-size-m, 14px);
    font-weight: var(--ha-font-weight-medium, 500);
    margin: 16px 4px 8px;
    color: var(--secondary-text-color);
  }
  .day:first-child {
    margin-top: 4px;
  }
  .source {
    display: block;
    font-size: var(--ha-font-size-s, 12px);
    color: var(--secondary-text-color);
    margin-top: 4px;
    overflow-wrap: anywhere;
  }
  @container (max-width: 240px) {
    header {
      padding: var(--ha-space-3, 12px);
      gap: var(--ha-space-2, 8px);
    }
    h2 {
      font-size: var(--ha-font-size-l, 16px);
    }
    .content {
      padding: 0 var(--ha-space-3, 12px) var(--ha-space-3, 12px);
    }
    .pickup {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--ha-space-2, 8px);
    }
    .hero .visual {
      width: 48px;
      height: 48px;
    }
    .hero .visual ha-icon {
      --mdc-icon-size: 28px;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    * {
      animation: none !important;
      transition: none !important;
    }
  }
  @media (forced-colors: active) {
    .pickup {
      border: 1px solid ButtonText;
    }
    .visual:before,
    .styled .visual:before {
      border-color: CanvasText;
    }
  }
`;
// src/model.ts
function ze(e) {
	if (!e || typeof e.type != "string") throw Error("Card type is required");
	if (e.entities !== void 0 && (!Array.isArray(e.entities) || e.entities.some((e) => typeof e != "string" || !/^calendar\.[\w]+$/.test(e)))) throw Error("Select calendar entities");
	for (let [t, n, r] of [[
		"days",
		1,
		366
	], [
		"max_items",
		1,
		100
	]]) {
		let i = e[t];
		if (i !== void 0 && (!Number.isInteger(i) || i < n || i > r)) throw Error(`${t}: ${n}–${r}`);
	}
	for (let t of ["include_types", "exclude_types"]) if (e[t] !== void 0 && (!Array.isArray(e[t]) || e[t].some((e) => typeof e != "string"))) throw Error(`${t} must be a list of names`);
	if (e.types !== void 0 && (!Array.isArray(e.types) || e.types.some((e) => !e || typeof e.type != "string" || [
		"name",
		"icon",
		"color",
		"picture"
	].some((t) => e[t] !== void 0 && typeof e[t] != "string")))) throw Error("types must contain waste type styles");
	if (e.language) try {
		new Intl.DateTimeFormat(e.language);
	} catch {
		throw Error("Invalid language");
	}
	return {
		...e,
		entities: e.entities ? [...new Set(e.entities)] : void 0
	};
}
function Be(e, t) {
	return t?.language || e?.locale?.language || e?.language || "en";
}
function q(e) {
	return e.locale?.time_zone === "local" ? Intl.DateTimeFormat().resolvedOptions().timeZone : e.config.time_zone;
}
function J(e, t) {
	let n = new Intl.DateTimeFormat("en-US", {
		timeZone: t,
		year: "numeric",
		month: "2-digit",
		day: "2-digit"
	}).formatToParts(e), r = (e) => n.find((t) => t.type === e).value;
	return `${r("year")}-${r("month")}-${r("day")}`;
}
function Y(e) {
	if (!/^\d{4}-\d{2}-\d{2}$/.test(e)) return NaN;
	let [t, n, r] = e.split("-").map(Number), i = /* @__PURE__ */ new Date(0);
	return i.setUTCFullYear(t, n - 1, r), i.setUTCHours(0, 0, 0, 0), i.toISOString().slice(0, 10) === e ? i.getTime() / 864e5 : NaN;
}
function Ve(e, t) {
	return (/* @__PURE__ */ new Date((Y(e) + t) * 864e5)).toISOString().slice(0, 10);
}
function He(e, t, n, r, i) {
	return e.flatMap((e) => {
		let a = e.start?.date;
		if (!a && e.start?.dateTime) {
			let t = new Date(e.start.dateTime);
			Number.isFinite(t.getTime()) && (a = J(t, n));
		}
		if (!a || !Number.isFinite(Y(a)) || typeof e.summary != "string" || !e.summary.trim()) return [];
		let o = Y(a) - Y(r);
		return o >= 0 && o < i ? [{
			date: a,
			type: e.summary,
			entity: t
		}] : [];
	});
}
function Ue(e, t) {
	let n = /* @__PURE__ */ new Set();
	return e.filter((e) => {
		if (t.include_types?.length && !t.include_types.includes(e.type) || t.exclude_types?.includes(e.type)) return !1;
		let r = JSON.stringify([
			e.date,
			e.type,
			e.entity
		]);
		return !n.has(r) && (n.add(r), !0);
	}).sort((e, t) => e.date.localeCompare(t.date) || e.type.localeCompare(t.type) || e.entity.localeCompare(t.entity));
}
function We(e, t) {
	let n = /* @__PURE__ */ new Map();
	for (let t of e) {
		let e = n.get(t.entity);
		(!e || t.date < e) && n.set(t.entity, t.date);
	}
	return e.filter((e) => e.date === n.get(e.entity)).sort((e, n) => t.indexOf(e.entity) - t.indexOf(n.entity) || e.type.localeCompare(n.type));
}
function Ge(e, t) {
	return t.types?.find((t) => t.type === e.type) ?? { type: e.type };
}
function Ke(e) {
	return e && (/^\/(?!\/)/.test(e) || /^https:\/\//i.test(e)) ? e : void 0;
}
function qe(e, t) {
	return new Intl.DateTimeFormat(t, {
		timeZone: "UTC",
		weekday: "short",
		month: "short",
		day: "numeric"
	}).format(/* @__PURE__ */ new Date(`${e}T12:00:00Z`));
}
function Je(e, t, n) {
	return new Intl.RelativeTimeFormat(n, { numeric: "auto" }).format(Y(e) - Y(t), "day");
}
function Ye(e, t) {
	let n = e?.states?.[t];
	return !(!n || n.state === "unavailable" || n.state === "unknown" || n.attributes?.restored);
}
function Xe(e) {
	return e && typeof CSS < "u" && typeof CSS.supports == "function" && CSS.supports("color", e) ? e : void 0;
}
function X(e, t) {
	let n = e?.states[t];
	return n && (e?.formatEntityName?.(n) || n.attributes.friendly_name) || t;
}
// src/localize.ts
var Z = {
	en: {
		appearance: "Appearance",
		filters: "Filters",
		next: "Next collection",
		schedule: "Collection schedule",
		bins: "Your bins",
		loading: "Loading collections…",
		empty: "No collections in this period",
		choose: "Select your waste collection calendars in the card editor.",
		error: "Could not load collections",
		partial: "Some calendars could not be loaded",
		retry: "Retry",
		calendar: "Calendar",
		title: "Title",
		entities: "Calendars",
		days: "Days ahead",
		max_items: "Maximum items",
		show_countdown: "Show countdown",
		show_date: "Show date",
		show_icons: "Show icons",
		show_pictures: "Show pictures",
		show_colors: "Show colours",
		types: "Waste type styles",
		include_types: "Only these waste types",
		exclude_types: "Hide these waste types",
		language: "Language (optional)",
		type: "Provider waste type",
		name: "Display name",
		icon: "Icon",
		color: "Colour",
		picture: "Image URL"
	},
	de: {
		appearance: "Darstellung",
		filters: "Filter",
		next: "Nächste Abholung",
		schedule: "Abfuhrkalender",
		bins: "Ihre Tonnen",
		loading: "Abholungen werden geladen…",
		empty: "Keine Abholungen in diesem Zeitraum",
		choose: "Wählen Sie Ihre Abfallkalender im Karteneditor aus.",
		error: "Abholungen konnten nicht geladen werden",
		partial: "Einige Kalender konnten nicht geladen werden",
		retry: "Erneut versuchen",
		calendar: "Kalender",
		title: "Titel",
		entities: "Kalender",
		days: "Tage im Voraus",
		max_items: "Maximale Einträge",
		show_countdown: "Countdown anzeigen",
		show_date: "Datum anzeigen",
		show_icons: "Symbole anzeigen",
		show_pictures: "Bilder anzeigen",
		show_colors: "Farben anzeigen",
		types: "Abfallarten gestalten",
		include_types: "Nur diese Abfallarten",
		exclude_types: "Diese Abfallarten ausblenden",
		language: "Sprache (optional)",
		type: "Abfallart des Anbieters",
		name: "Anzeigename",
		icon: "Symbol",
		color: "Farbe",
		picture: "Bild-URL"
	},
	fr: {
		appearance: "Apparence",
		filters: "Filtres",
		next: "Prochaine collecte",
		schedule: "Calendrier des collectes",
		bins: "Vos bacs",
		loading: "Chargement des collectes…",
		empty: "Aucune collecte sur cette période",
		choose: "Sélectionnez vos calendriers de collecte dans l’éditeur.",
		error: "Impossible de charger les collectes",
		partial: "Certains calendriers n’ont pas pu être chargés",
		retry: "Réessayer",
		calendar: "Calendrier",
		title: "Titre",
		entities: "Calendriers",
		days: "Jours à venir",
		max_items: "Nombre maximal",
		show_countdown: "Afficher le compte à rebours",
		show_date: "Afficher la date",
		show_icons: "Afficher les icônes",
		show_pictures: "Afficher les images",
		show_colors: "Afficher les couleurs",
		types: "Styles des déchets",
		include_types: "Uniquement ces déchets",
		exclude_types: "Masquer ces déchets",
		language: "Langue (facultatif)",
		type: "Type de déchet du fournisseur",
		name: "Nom affiché",
		icon: "Icône",
		color: "Couleur",
		picture: "URL de l’image"
	},
	it: {
		appearance: "Aspetto",
		filters: "Filtri",
		next: "Prossima raccolta",
		schedule: "Calendario raccolta",
		bins: "I tuoi bidoni",
		loading: "Caricamento raccolte…",
		empty: "Nessuna raccolta in questo periodo",
		choose: "Seleziona i calendari dei rifiuti nell’editor.",
		error: "Impossibile caricare le raccolte",
		partial: "Impossibile caricare alcuni calendari",
		retry: "Riprova",
		calendar: "Calendario",
		title: "Titolo",
		entities: "Calendari",
		days: "Giorni futuri",
		max_items: "Numero massimo",
		show_countdown: "Mostra conto alla rovescia",
		show_date: "Mostra data",
		show_icons: "Mostra icone",
		show_pictures: "Mostra immagini",
		show_colors: "Mostra colori",
		types: "Stili dei rifiuti",
		include_types: "Solo questi rifiuti",
		exclude_types: "Nascondi questi rifiuti",
		language: "Lingua (opzionale)",
		type: "Tipo di rifiuto del fornitore",
		name: "Nome visualizzato",
		icon: "Icona",
		color: "Colore",
		picture: "URL immagine"
	}
};
function Q(e, t) {
	return (Z[e.toLowerCase().split("-")[0]] ?? Z.en)[t];
}
// src/editor.ts
var Ze = class extends V {
	static properties = {
		hass: { attribute: !1 },
		config: { state: !0 }
	};
	setConfig(e) {
		this.config = { ...e };
	}
	render() {
		if (!this.config || !this.hass) return j``;
		let e = Be(this.hass, this.config), t = (t) => Q(e, t.name) ?? t.name, n = [
			{
				name: "title",
				selector: { text: {} }
			},
			{
				name: "entities",
				required: !0,
				selector: { entity: {
					multiple: !0,
					filter: {
						domain: "calendar",
						integration: "waste_collection_schedule"
					},
					reorder: !0
				} }
			},
			{
				name: "days",
				selector: { number: {
					min: 1,
					max: 366,
					mode: "box"
				} }
			},
			{
				name: "max_items",
				selector: { number: {
					min: 1,
					max: 100,
					mode: "box"
				} }
			},
			...[
				"show_countdown",
				"show_date",
				"show_icons",
				"show_pictures",
				"show_colors"
			].map((e) => ({
				name: e,
				selector: { boolean: {} }
			})),
			{
				name: "types",
				selector: { object: {
					multiple: !0,
					fields: {
						type: {
							label: Q(e, "type"),
							required: !0,
							selector: { text: {} }
						},
						name: {
							label: Q(e, "name"),
							selector: { text: {} }
						},
						icon: {
							label: Q(e, "icon"),
							selector: { icon: {} }
						},
						color: {
							label: Q(e, "color"),
							selector: { text: {} }
						},
						picture: {
							label: Q(e, "picture"),
							selector: { text: {} }
						}
					}
				} }
			},
			...["include_types", "exclude_types"].map((e) => ({
				name: e,
				selector: { select: {
					multiple: !0,
					custom_value: !0,
					options: []
				} }
			})),
			{
				name: "language",
				selector: { text: {} }
			}
		], r = (t, n) => ({
			type: "expandable",
			name: "",
			flatten: !0,
			title: Q(e, t),
			schema: n
		}), i = [
			...n.slice(0, 4),
			r("appearance", [...n.slice(4, 9), n[12]]),
			r("types", n.slice(9, 10)),
			r("filters", n.slice(10, 12))
		];
		return j`<ha-form
      .hass=${this.hass}
      .data=${{
			days: this.config.type.includes("bins-card") ? 90 : 30,
			max_items: 12,
			show_countdown: !0,
			show_date: !0,
			show_icons: !0,
			show_pictures: !0,
			show_colors: !0,
			...this.config
		}}
      .schema=${i}
      .computeLabel=${t}
      @value-changed=${(e) => {
			e.stopPropagation(), this.config = {
				...e.detail.value,
				type: this.config.type
			}, this.dispatchEvent(new CustomEvent("config-changed", {
				detail: { config: this.config },
				bubbles: !0,
				composed: !0
			}));
		}}
    ></ha-form>`;
	}
};
customElements.get("waste-collection-card-editor") || customElements.define("waste-collection-card-editor", Ze);
// src/cards.ts
var Qe = /* @__PURE__ */ new WeakMap();
function $e(e, t, n, r, i, a) {
	let o = Qe.get(e.callApi);
	o || (o = /* @__PURE__ */ new Map(), Qe.set(e.callApi, o));
	let s = JSON.stringify([
		t,
		n,
		r,
		a
	]), c = o.get(s);
	if (!i && c && Date.now() - c.at < 3e4) return c.promise;
	let l = e.callApi("GET", `calendars/${t}?start=${encodeURIComponent(n)}&end=${encodeURIComponent(r)}`), u = {
		at: Date.now(),
		promise: l
	};
	return o.set(s, u), o.size > 100 && o.delete(o.keys().next().value), l.catch(() => {
		o.get(s) === u && o.delete(s);
	}), l;
}
async function et(e) {
	return (await e.callWS({ type: "config/entity_registry/list" })).filter((t) => t.platform === "waste_collection_schedule" && t.entity_id.startsWith("calendar.") && !t.disabled_by && !t.hidden_by && Ye(e, t.entity_id)).map((e) => e.entity_id);
}
var $ = class extends V {
	static properties = {
		hass: { attribute: !1 },
		config: { state: !0 },
		pickups: { state: !0 },
		loading: { state: !0 },
		failed: { state: !0 },
		now: { state: !0 }
	};
	static styles = Re;
	mode = "next";
	static defaultDays = 30;
	generation = 0;
	timer;
	unsubscribe;
	lastSignature = "";
	lastRefresh = 0;
	constructor() {
		super(), this.config = { type: "custom:waste-collection-next-card" }, this.pickups = [], this.loading = !1, this.failed = [], this.now = /* @__PURE__ */ new Date();
	}
	static getConfigElement() {
		return document.createElement("waste-collection-card-editor");
	}
	static async getStubConfig(e) {
		let t = [];
		try {
			t = await et(e);
		} catch {}
		return {
			entities: t,
			days: this.defaultDays,
			max_items: 12
		};
	}
	get days() {
		return this.config.days ?? this.constructor.defaultDays;
	}
	setConfig(e) {
		this.config = ze(e), this.lastSignature = "", this.pickups = [], this.failed = [], this.generation++, this.isConnected && this.refresh();
	}
	getCardSize() {
		return this.mode === "schedule" ? 5 : 4;
	}
	getGridOptions() {
		return {
			columns: 12,
			rows: this.mode === "schedule" ? 5 : "auto",
			min_columns: 6,
			min_rows: this.mode === "next" ? 3 : 4
		};
	}
	connectedCallback() {
		super.connectedCallback();
		let e = new CustomEvent("context-request", {
			bubbles: !0,
			composed: !0,
			cancelable: !0
		});
		e.context = "states", e.subscribe = !0, e.callback = (e, t) => {
			this.unsubscribe = t, this.checkStates(e);
		}, this.dispatchEvent(e), this.timer = setInterval(() => {
			this.now = /* @__PURE__ */ new Date(), (Date.now() - this.lastRefresh >= 3e5 || this.signature() !== this.lastSignature) && this.refresh();
		}, 6e4), this.refresh();
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this.generation++, clearInterval(this.timer), this.unsubscribe?.(), this.unsubscribe = void 0;
	}
	updated(e) {
		e.has("hass") && this.hass && this.checkStates(this.hass.states);
	}
	update(e) {
		let t = this.shadowRoot?.activeElement;
		super.update(e), t instanceof HTMLButtonElement && t.classList.contains("pickup") && t.isConnected && this.shadowRoot?.activeElement !== t && t.focus({ preventScroll: !0 });
	}
	signature(e = this.hass?.states) {
		return this.hass ? JSON.stringify([
			this.config.entities,
			this.days,
			J(this.now, q(this.hass)),
			q(this.hass),
			this.config.entities?.map((t) => [e?.[t]?.state, e?.[t]?.last_updated])
		]) : "";
	}
	checkStates(e) {
		this.signature(e) !== this.lastSignature && this.refresh(e);
	}
	async refresh(e = this.hass?.states, t = !1) {
		let n = this.hass;
		if (!n || !this.isConnected) return;
		let r = ++this.generation;
		this.lastSignature = this.signature(e), this.lastRefresh = Date.now();
		let i = this.config.entities ?? [];
		if (!i.length) {
			this.loading = !1, this.pickups = [], this.failed = [];
			return;
		}
		this.loading = !0;
		let a = this.days, o = q(n), s = J(/* @__PURE__ */ new Date(), o), c = `${Ve(s, -1)}T00:00:00Z`, l = `${Ve(s, a + 1)}T00:00:00Z`, u = await Promise.allSettled(i.map(async (r) => {
			if (!e?.[r] || ["unavailable", "unknown"].includes(e[r].state)) throw Error(r);
			return He(await $e(n, r, c, l, t, JSON.stringify([e[r].state, e[r].last_updated])), r, o, s, a);
		}));
		r === this.generation && this.isConnected && (this.pickups = u.flatMap((e) => e.status === "fulfilled" ? e.value : []), this.failed = u.flatMap((e, t) => e.status === "rejected" ? [i[t]] : []), this.now = /* @__PURE__ */ new Date(), this.loading = !1);
	}
	moreInfo(e) {
		this.dispatchEvent(new CustomEvent("hass-more-info", {
			detail: { entityId: e },
			bubbles: !0,
			composed: !0
		}));
	}
	pickup(e, t, n, r) {
		let i = Ge(e, this.config), a = this.hass?.states[e.entity]?.attributes, o = a?.waste_types?.[e.type], s = i.icon || o?.icon || a?.icon || "mdi:trash-can-outline", c = this.config.show_pictures === !1 ? void 0 : Ke(i.picture) || Ke(o?.picture), l = this.config.show_colors === !1 ? void 0 : Xe(i.color) ?? Xe(o?.color), u = i.name || e.type, d = this.config.show_icons !== !1;
		return j`<button
      class=${l ? "pickup styled" : "pickup"}
      style=${Oe({ "--bin-color": l })}
      @click=${() => this.moreInfo(e.entity)}
    >
      ${c || d ? j`<span class="visual" aria-hidden="true"
            >${c ? Fe(JSON.stringify([c, d]), j`<img
                      src=${c}
                      alt=""
                      loading="lazy"
                      @error=${(e) => {
			let t = e.target;
			t.hidden = !0, d && t.nextElementSibling?.removeAttribute("hidden");
		}}
                    />${d ? j`<ha-icon hidden .icon=${s}></ha-icon>` : N}`) : j`<ha-icon .icon=${s}></ha-icon>`}</span
          >` : N}
      <span class="words"
        ><span class="name">${u}</span>
        ${this.config.show_countdown === !1 ? N : j`<span class="when"
              >${Je(e.date, n, t)}</span
            >`}
        ${this.config.show_date === !1 ? N : j`<span class="meta"
              ><time datetime=${e.date}
                >${qe(e.date, t)}</time
              ></span
            >`}
        ${r ? j`<span class="source">${X(this.hass, e.entity)}</span>` : N}
      </span>
    </button>`;
	}
	render() {
		let e = Be(this.hass, this.config), t = J(this.now, this.hass ? q(this.hass) : "UTC"), n = Ue(this.pickups, this.config).filter((e) => e.date >= t), r = this.config.entities ?? [], i = r.length > 1, a = n;
		if (this.mode === "next" && (a = We(n, r)), this.mode === "bins") {
			let e = /* @__PURE__ */ new Set();
			a = n.filter((t) => {
				let n = JSON.stringify([t.entity, t.type]);
				return !e.has(n) && (e.add(n), !0);
			});
		}
		a = a.slice(0, this.config.max_items ?? 12);
		let o = this.failed.length === (this.config.entities?.length ?? 0) && this.failed.length > 0, s = "";
		return j`<div class="frame">
      <ha-card
        ><header>
          <ha-icon icon="mdi:recycle" aria-hidden="true"></ha-icon>
          <h2>${this.config.title ?? Q(e, this.mode)}</h2>
        </header>
        <div class="content" aria-busy=${this.loading}>
          ${this.config.entities?.length ? this.loading && this.pickups.length === 0 && this.failed.length === 0 ? j`<div class="state" role="status">
                  ${Q(e, "loading")}
                </div>` : j`
                  ${this.failed.length ? j`<div class="state error" role="status">
                        <ha-icon
                          icon="mdi:alert-circle-outline"
                          aria-hidden="true"
                        ></ha-icon>
                        <div>
                          ${Q(e, o ? "error" : "partial")}
                          <div class="failed">
                            ${this.failed.map((e) => X(this.hass, e)).join(", ")}
                          </div>
                          <button
                            class="retry"
                            @click=${() => this.refresh(this.hass?.states, !0)}
                          >
                            ${Q(e, "retry")}
                          </button>
                        </div>
                      </div>` : N}
                  ${!a.length && !o ? j`<div class="state" role="status">
                        ${Q(e, "empty")}
                      </div>` : N}
                  <div
                    class=${this.mode === "bins" ? "bins" : this.mode === "next" ? "list hero" : "list"}
                  >
                    ${Le(a, (e) => JSON.stringify([
			e.entity,
			e.type,
			e.date
		]), (n) => {
			let r = this.mode === "schedule" ? n.date : this.mode === "next" && i ? n.entity : "", a = r && s !== r;
			return s = r, j`${a ? j`<h3 class="day">
                              ${this.mode === "schedule" ? qe(n.date, e) : X(this.hass, n.entity)}
                            </h3>` : N}${this.pickup(n, e, t, i && this.mode !== "next")}`;
		})}
                  </div>
                ` : j`<div class="state" role="status">
                ${Q(e, "choose")}
              </div>`}
        </div></ha-card
      >
    </div>`;
	}
}, tt = class extends $ {
	mode = "next";
}, nt = class extends $ {
	mode = "schedule";
}, rt = class extends $ {
	static defaultDays = 90;
	mode = "bins";
};
for (let [e, t, n, r] of [
	[
		"waste-collection-next-card",
		tt,
		"Waste Collection · Next pickup",
		"All collections on the next collection day"
	],
	[
		"waste-collection-schedule-card",
		nt,
		"Waste Collection · Schedule",
		"Upcoming collections grouped by day"
	],
	[
		"waste-collection-bins-card",
		rt,
		"Waste Collection · Bins",
		"The next pickup for each waste type"
	]
]) customElements.get(e) || customElements.define(e, t), window.customCards ??= [], window.customCards.some((t) => t.type === e) || window.customCards.push({
	type: e,
	name: n,
	description: r,
	preview: !0
});
export { $ as WasteCard };
