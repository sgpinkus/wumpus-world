import { EventEmitter } from 'node:events';
import { WumpusWorld } from './wumpus-world-game-model/index.js';


async function sleep(n=1000) {
  return new Promise((resolve) => setTimeout(resolve, n));
}

/**
 * Runs the world and generates signal for observers when things happen.
 * The WumpusWorld is just a data container and has no concept of running state.
 */
class Wrapper {
  /** @type {WumpusWorld} */
  world;
  turnTime = 400; // ms.
  runTurns = 5;
  events = new EventEmitter();
  /** @type {('INIT'|'RUNNING'|'STOPPING'|'STOPPED')} */
  state = 'INIT';
  eventTypes = ['new-game', 'game-running', 'game-stopped', 'turn-start', 'turn-end', 'new-agent'];
  allow_new_agents_after_init = true
  removeDeadAgents = true

  constructor() {
    this.reset();
  }

  addAgent() {
    if(this.state !== 'INIT' && !this.allow_new_agents_after_init) throw new Error('Cant add agent. Game already started');
    const agent = this.world.addAgent();
    this.events.emit('new-agent', agent);
    return agent;
  }

  /**
   * Try and remove agent but dont let agent state disappeared in the middle of
   * a game. People wnat to know.
   * @param {number} agentId
   * @returns
   */
  removeAgent(agentId) {
    let agent = this.world.getAgent(agentId);
    if(this.state === 'INIT' || this.removeDeadAgents) {
      this.world.removeAgent(agentId);
      this.events.emit('agent-removed', { agentId });
    } else {
      agent = this.world.setOnAgent(agentId, { gone: true });
      this.events.emit('new-agent', agent);
    }
  }

  async _run (runTurns) {
    try {
      this.state = 'RUNNING';
      this.events.emit('game-running');
      // @ts-ignore
      for(let i = 0; i < runTurns && this.state !== 'STOPPING'; i++) {
        this.events.emit('turn-start', { i });
        await sleep(this.turnTime); // Wait for inbound actions.
        this.events.emit('turn-end', { i });
      }
    } finally {
      this.state = 'STOPPED';
      this.events.emit('game-stopped');
    }
  }

  /**
   * @param {number | undefined} runTurns
   * @returns
   */
  run(runTurns = undefined) {
    if(this.state === 'RUNNING') throw new Error('Game already running');
    if(!this.world.agents.length) throw new Error('Game cant run with no agents');
    setTimeout(() => this._run(runTurns ?? this.runTurns), 0);
    return this.world.toSerial();
  }

  step() {
    return this.run(1);
  }

  stop() {
    if(this.state === 'RUNNING') this.state = 'STOPPING';
  }

  reset() {
    this.state = 'INIT';
    this.world = new WumpusWorld(10, 0.2, 0.2, 4);
    this.events.emit('new-game');
  }

  action(agentId, type, payload) {
    return this.world.action(agentId, type, payload);
  }

  meta() {
    return this.world.meta();
  }

  toSerial() {
    return {
      ...this.world.toSerial(),
      runTurns: this.runTurns,
      turnTime: this.turnTime,
      state: this.state,
    };
  }

  getAgent(agentId) {
    return this.world.getAgent(agentId);
  }

  off(listener) {
    this.eventTypes.forEach(v => this.events.off(v, listener)); // This doesn't E on EventEmitter?!
  }
}

export default new Wrapper();