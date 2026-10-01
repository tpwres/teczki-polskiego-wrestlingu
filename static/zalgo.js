// Note: Created with heavy AI involvement - human was guiding each iteration and supplying ideas

class Zalgoifier {
  constructor({
    root = document.body, // Element or selector
    interval = 200, // ms between successive mutations
    charsPerStep = 3, // how many chars to apply each step
    zalgoIntensity = 4, // how many glyphs to apply to characters each step
    hoverRestoreSelectors = 'a, li', // these elements can be cleaned by just hovering cursor
    excludeSelectors = 'nav, footer, [role="navigation"]', // never touched - navigation etc
    zalgoChance = 0.9, // probability of each char being modified
    depthDecayFactor = 0.3, // avoid choosing already decorated characters
    duplicateMarkPenalty = 0.05, // avoid applying same marks more than once
    clearChance = 0.05, // chance to completely clear instead of decorating
    frakturChance = 0.02 // probability for lowercase a-z to convert to Fraktur
  } = {}) {
    this.root = typeof root === 'string' ? document.querySelector(root) : root;
    this.intervalMs = interval;
    this.charsPerStep = charsPerStep;
    this.zalgoIntensity = zalgoIntensity;
    this.zalgoChance = zalgoChance;
    this.hoverRestoreSelectors = hoverRestoreSelectors;
    this.excludeSelectors = excludeSelectors;
    this.depthDecayFactor = depthDecayFactor;
    this.duplicateMarkPenalty = duplicateMarkPenalty;
    this.clearChance = clearChance;
    this.frakturChance = frakturChance;

    this.timer = null;
    this.textNodes = [];
    this.originalTexts = new WeakMap();

    this.safeMarkRanges = [
      [0x0300, 0x036F], // Combining Diacritical Marks
      [0x1AB0, 0x1ACE], // Combining Diacritical Marks Extended
      [0x1DC0, 0x1DFE], // Combining Diacritical Marks Supplement
    ];

    this.punctuationRegex = /[\p{P}\p{S}]/u;

    // Initialize Fraktur mapping tables
    this.initFrakturMaps();

    this.handleMouseOver = this.handleMouseOver.bind(this);
  }

  /**
   * Initializes standard and bold Unicode Fraktur lookup tables for a-z using sequential ranges.
   */
  initFrakturMaps() {
    // Mathematical Fraktur lowercase range (U+1D51E - U+1D537)
    const frakturLowerStart = 0x1D51E;
    this.stdFrakturMap = {};
    for (let i = 0; i < 26; i++) {
      const char = String.fromCharCode(97 + i);
      this.stdFrakturMap[char] = String.fromCodePoint(frakturLowerStart + i);
    }

    // Mathematical Bold Fraktur lowercase range (U+1D586 - U+1D59F)
    const boldFrakturLowerStart = 0x1D586;
    this.boldFrakturMap = {};
    for (let i = 0; i < 26; i++) {
      const char = String.fromCharCode(97 + i);
      this.boldFrakturMap[char] = String.fromCodePoint(boldFrakturLowerStart + i);
    }
  }

  /**
   * Helper to check if a character is already a standard or bold Fraktur symbol.
   */
  isFraktur(char) {
    const cp = char.codePointAt(0);
    return (
      (cp >= 0x1D51E && cp <= 0x1D537) || // Standard Fraktur
      (cp >= 0x1D586 && cp <= 0x1D59F)    // Bold Fraktur
    );
  }

  /**
   * Character validation method.
   */
  isValidChar(char) {
    if (!char || !/\S/.test(char)) return false; // Skip whitespace & empty chars

    const codePoint = char.codePointAt(0);

    // Skip Regional Indicator Symbols (Flags)
    if (codePoint >= 0x1F1E6 && codePoint <= 0x1F1FF) return false;

    // Skip characters that have already been converted to Fraktur
    if (this.isFraktur(char)) return false;

    return true;
  }

  isPunctuation(char) {
    return this.punctuationRegex.test(char);
  }

  isCombiningMark(codePoint) {
    return this.safeMarkRanges.some(([min, max]) => codePoint >= min && codePoint <= max);
  }

  /**
   * Attempts to convert a base character to standard or bold Fraktur.
   * If successful, replaces the base character and strips attached Zalgo marks.
   * @returns {boolean} True if transformed, false otherwise.
   */
  tryTransformToFraktur(symbols, target) {
    const baseChar = symbols[target.index];

    if (!/^[a-z]$/.test(baseChar) || Math.random() >= this.frakturChance) {
      return false;
    }

    const useBold = Math.random() < 0.5;
    const map = useBold ? this.boldFrakturMap : this.stdFrakturMap;
    const frakturChar = map[baseChar];

    // Replace base character with Fraktur & clear all attached Zalgo marks
    symbols.splice(target.index, 1 + target.existingMarks.length, frakturChar);
    return true;
  }

  getRandomWeightedMark(existingMarksSet) {
    const candidates = [];
    for (const [min, max] of this.safeMarkRanges) {
      for (let cp = min; cp <= max; cp++) {
        const mark = String.fromCharCode(cp);
        const weight = existingMarksSet.has(mark) ? this.duplicateMarkPenalty : 1.0;
        candidates.push({ mark, weight });
      }
    }

    const totalWeight = candidates.reduce((sum, c) => sum + c.weight, 0);
    let randomVal = Math.random() * totalWeight;

    for (const c of candidates) {
      if (randomVal < c.weight) {
        return c.mark;
      }
      randomVal -= c.weight;
    }

    return candidates[candidates.length - 1].mark;
  }

  addSoftWeightedZalgo(char, existingMarks, count) {
    const markSet = new Set(existingMarks);
    let result = char;

    for (let i = 0; i < count; i++) {
      const mark = this.getRandomWeightedMark(markSet);
      markSet.add(mark);
      result += mark;
    }
    return result;
  }

  collectTextNodes() {
    this.textNodes = [];
    if (!this.root) return;

    const walker = document.createTreeWalker(
      this.root,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;

          const tag = parent.tagName.toLowerCase();
          if (['script', 'style', 'noscript', 'textarea', 'input'].includes(tag)) {
            return NodeFilter.FILTER_REJECT;
          }

          if (this.excludeSelectors && parent.closest(this.excludeSelectors)) {
            return NodeFilter.FILTER_REJECT;
          }

          return node.nodeValue.trim().length > 0
            ? NodeFilter.FILTER_ACCEPT
            : NodeFilter.FILTER_SKIP;
        }
      }
    );

    while (walker.nextNode()) {
      const node = walker.currentNode;
      this.textNodes.push(node);
      this.originalTexts.set(node, node.nodeValue);
    }
  }

  getWeightedCharLocations() {
    const locations = [];

    for (const node of this.textNodes) {
      if (this.hoverRestoreSelectors) {
        const parentTarget = node.parentElement?.closest(this.hoverRestoreSelectors);
        if (parentTarget && parentTarget.matches(':hover')) continue;
      }

      const text = node.nodeValue;
      if (!text) continue;

      const symbols = Array.from(text);
      let j = 0;

      while (j < symbols.length) {
        const baseChar = symbols[j];

        if (!this.isValidChar(baseChar)) {
          j++;
          continue;
        }

        const baseIndex = j;
        const existingMarks = [];
        j++;

        // Collect existing combining marks following this character
        while (j < symbols.length) {
          const markChar = symbols[j];
          const codePoint = markChar.codePointAt(0);
          if (this.isCombiningMark(codePoint)) {
            existingMarks.push(markChar);
            j++;
          } else {
            break;
          }
        }

        const weight = Math.pow(this.depthDecayFactor, existingMarks.length);

        locations.push({
          node,
          index: baseIndex,
          existingMarks,
          weight
        });
      }
    }

    return locations;
  }

  pickWeightedLocation(locations) {
    const totalWeight = locations.reduce((sum, loc) => sum + loc.weight, 0);
    if (totalWeight <= 0) return null;

    let randomVal = Math.random() * totalWeight;
    for (const loc of locations) {
      if (randomVal < loc.weight) {
        return loc;
      }
      randomVal -= loc.weight;
    }

    return locations[locations.length - 1];
  }

  handleMouseOver(e) {
    if (!this.hoverRestoreSelectors) return;
    const targetEl = e.target.closest(this.hoverRestoreSelectors);
    if (!targetEl) return;

    for (const node of this.textNodes) {
      if (targetEl.contains(node) && this.originalTexts.has(node)) {
        node.nodeValue = this.originalTexts.get(node);
      }
    }
  }

  step() {
    for (let i = 0; i < this.charsPerStep; i++) {
      const locations = this.getWeightedCharLocations();
      if (locations.length === 0) return;

      const target = this.pickWeightedLocation(locations);
      if (!target) continue;

      const text = target.node.nodeValue;
      if (!text) continue;

      const symbols = Array.from(text);
      const baseChar = symbols[target.index];
      if (!baseChar || !this.isValidChar(baseChar)) continue;

      // 1. Delete punctuation
      if (this.isPunctuation(baseChar)) {
        const deleteLength = 1 + target.existingMarks.length;
        symbols.splice(target.index, deleteLength);
      }
      // 2. Random conversion to standard or bold Fraktur
      else if (this.tryTransformToFraktur(symbols, target)) {
        // Transformation performed inside method
      }
      // 3. Clear attached Zalgo marks based on clearChance
      else if (target.existingMarks.length > 0 && Math.random() < this.clearChance) {
        symbols.splice(target.index + 1, target.existingMarks.length);
      }
      // 4. Apply standard Zalgo decoration
        else if (Math.random() < this.zalgoChance) {
        symbols[target.index] = this.addSoftWeightedZalgo(baseChar, target.existingMarks, this.zalgoIntensity);
      }

      target.node.nodeValue = symbols.join('');
    }
  }

  start() {
    this.stop();
    this.collectTextNodes();
    if (this.textNodes.length === 0) return;

    if (this.hoverRestoreSelectors) {
      document.addEventListener('mouseover', this.handleMouseOver, true);
    }

    this.timer = setInterval(() => this.step(), this.intervalMs);
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    document.removeEventListener('mouseover', this.handleMouseOver, true);
  }

  restoreAll() {
    for (const node of this.textNodes) {
      if (this.originalTexts.has(node)) {
        node.nodeValue = this.originalTexts.get(node);
      }
    }
  }
}

/**
 * Presets for Zalgoifier
 * Each function returns a configured Zalgoifier instance ready to call .start()
 */

/**
 * 1. Slow Creep
 * Subtle, low-intensity corruption that slowly nibbles at punctuation
 * and sparingly converts characters. Ideal for long ambient sessions.
 */
function createSlowCreepPreset(root = document.body) {
  return new Zalgoifier({
    root,
    interval: 350,
    charsPerStep: 1,
    zalgoIntensity: 1,
    clearChance: 0.15,       // High recovery rate keeps text readable
    frakturChance: 0.01,     // Rare font mutations
    depthDecayFactor: 0.2
  });
}

/**
 * 2. Gothic Decay
 * High Fraktur mutation rate with moderate Zalgo diacriticals.
 * Quickly transforms modern readable text into an ancient, corrupted manuscript.
 */
function createGothicDecayPreset(root = document.body) {
  return new Zalgoifier({
    root,
    interval: 150,
    charsPerStep: 2,
    zalgoIntensity: 1,
    clearChance: 0.02,
    frakturChance: 0.75,     // Heavy Fraktur conversion rate
    depthDecayFactor: 0.35
  });
}

/**
 * 3. Void Consumption
 * High punctuation deletion rate paired with heavy vertical Zalgo stacks.
 * Rapidly strips structure while swarming the page in diacritical noise.
 */
function createVoidConsumptionPreset(root = document.body) {
  return new Zalgoifier({
    root,
    interval: 80,
    charsPerStep: 5,
    zalgoIntensity: 8,       // Dense, tall Zalgo spikes
    clearChance: 0.005,      // Almost no self-cleaning
    frakturChance: 0.05,
    depthDecayFactor: 0.6    // Low decay allows heavy stacking on same characters
  });
}

/**
 * 4. Glitch Flickers
 * Fast step rate with high clear chance and high character throughput.
 * Text constantly mutates and resets in real-time like a loose video cable.
 */
function createGlitchFlickerPreset(root = document.body) {
  return new Zalgoifier({
    root,
    interval: 10,
    charsPerStep: 2,
    zalgoIntensity: 1,
    clearChance: 0.99,       // Frequent resets create a flickering digital artifact effect
    zalgoChance: 0.1,
    frakturChance: 0.0, // No fraktur
    depthDecayFactor: 0.25
  });
}

