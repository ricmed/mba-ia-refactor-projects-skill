/**
 * Substitui o `globalCache = {}` mutável de módulo (estado global compartilhado
 * sem encapsulamento) por uma instância única com API própria e ciclo de vida
 * claro. Ver anti-pattern "Estado Global Mutável" no catálogo.
 */
class Cache {
    #store = new Map();

    set(key, value) {
        this.#store.set(key, value);
    }

    get(key) {
        return this.#store.get(key);
    }

    has(key) {
        return this.#store.has(key);
    }
}

module.exports = new Cache();
