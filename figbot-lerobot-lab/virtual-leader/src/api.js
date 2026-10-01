export class API {
  constructor() { this.token = null; }
  async state() {
    const result = await fetch('/api/state', {cache: 'no-store'});
    if (!result.ok) throw new Error('Yerel sürücüye ulaşılamadı.');
    const value = await result.json(); this.token = value.token; return value;
  }
  async action(route, value = {}) {
    const result = await fetch('/api/' + route, {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-Figbot-Token': this.token ?? ''},
      body: JSON.stringify(value), signal: AbortSignal.timeout(route === 'emergency' ? 6000 : 2000),
    });
    const body = await result.json();
    if (!result.ok) throw new Error(body.error || 'İşlem başarısız.');
    return body;
  }
}
