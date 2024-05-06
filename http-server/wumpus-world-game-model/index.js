import lodash from 'lodash';
const { pickBy, sampleSize } = lodash;

/**
 * @typedef Agent
 * @property {number} id
 * @property {string} tag
 * @property {[number, number]} location
 * @property {number} arrows
 * @property {number} score
 * @property {number} moves
 */

/**
 * @typedef {'E'|'NE'|'N'|'NW'|'W'|'SW'|'S'|'SE'} Direction
 */

/**
 * @typedef {'MOVE'|'PICK'|'SHOOT'} Action
 */
// export const Directions = ['E', 'NE', 'N', 'NW', 'W', 'SW', 'S', 'SE'];
export const Directions = {
  E: [1,0],
  N: [0,-1],
  W: [-1, 0],
  S: [0, 1],
}
export const BaseAgent = ['id', 'tag', 'location'];
export const AgentDefaults = { score: 0, moves: 0, arrows: 3 };

export function assertIsDirection(v) {
  if(!Object.keys(Directions).includes(v)) throw new Error(`Invalid direction (${v})`);
}

/**
 *
 * @param {number} x
 * @param {number} y
 * @param {number} n
 * @returns {{[k in Direction]?: [number, number]}}
 */
export function adjacent(x, y, n) {
  /** @type {{[k in Direction]?: [number, number]}} */
  let _raw = Object.fromEntries(Object.entries(Directions).map(([k, v]) => ([k, [v[0]+x, v[1]+y]])))
  return Object.fromEntries(
    Object.entries(_raw).filter(([_k, [x, y]]) => !(x < 0 || x >= n || y < 0 || y >= n))
  );
}

/**
 *
 * @param {number} x
 * @param {number} y
 * @param {number} n
 * @returns
 */
export function cellIndex(x, y, n) {
  if(x < 0 || x >= n) throw new Error(`X must be between [0,${n}] (${x})`);
  if(y < 0 || y >= n) throw new Error(`Y must be between [0,${n}] (${y})`);
  return x + y*n;
}

export function gridIndex(i, n) {
  return [i%n, Math.floor(i/n)]
}

function range(a, b) {
  const [min, max] = b !== undefined ? [a, b] : [0, a];
  return max > min ? Array.from(Array(max - min)).map((_v, i) => i + min) : [];
}

/**
 * @class
 * @classdesc State for a multiplayer (agent) wumpus world plus basic mutators.
 * There is no end to a started game - upto client to decide. Game class also does
 * not enforce an equal number of moves / agent - dido.
 */
export class WumpusWorld {
  /** @type {number} */
  n = 0;
  /** @type {number} probability pit */
  pp = 0;
  /** @type {number} probability gold */
  pg = 0;
  /** @type {number} number of wumpus */
  dn = 3;
  /** @type {Set<string>[]} the grid. Each cell may contain a number of char strings indicating what's in them. */
  grid = [];
  /** @type {Agent[]} */
  agents = [];

  /**
   *
   * @param {number} n size of grid
   * @param {number} pp probability of pit.
   * @param {number} pg probability of gold.
   */
  constructor(n, pp=0.1, pg=0.1, dn = 3) {
    if(n <= 0 || n > 10) throw new Error(`Size must be between [0,10] (${n})`);
    if(pp < 0 || pp > 1) throw new Error(`Pit probability must be between [0,1] (${pp})`);
    if(pg < 0 || pg > 1) throw new Error(`Gold probability must be between [0,1] (${pg})`);
    this.n = n;
    this.pp = pp;
    this.pg = pg;
    this.dn = dn;
    this.grid = range(n*n).map(() => new Set([]));
    this.grid.forEach((cell, i) => {
      if(i != 0 && Math.random() < pp) {
        cell.add('P');
      }
    });
    this.grid.forEach((cell, i) => {
      if(i != 0 && Math.random() < pg) {
        cell.add('G');
      }
    });
    sampleSize(range(1,n*n), this.dn).forEach(i => {
      this.grid[i].add('W')
    });
  }

  /**
   *
   * @param {number} agentId
   * @param {Action} type
   * @param {any} args
   */
  action(agentId, type, args) {
    const agent = this.getAgent(agentId);
    /** @type {string[] | undefined} */
    let postPercepts = [];
    agent.moves += 1;
    if(type === 'MOVE') {
      postPercepts = this._move(agentId, args.direction);
    }
    else if(type === 'PICK') {
      postPercepts = this._pick(agentId, args.what);
    }
    else if(type === 'SHOOT') {
      postPercepts = this._shoot(agentId, args.direction);
    }
    else {
      throw new Error(`Invalid action type (${type})`);
    }
    return this.getAgentPercept(agentId, postPercepts);
  }

  /**
   *
   * @param {number} agentId
   * @param {Direction} direction
   */
  _move(agentId, direction) {
    assertIsDirection(direction);
    const agent = this.getAgent(agentId);
    const adj = adjacent(...agent.location, this.n);
    agent.score -= 1;
    if(adj[direction]) {
      this._gridReplace(agent.tag, agent.location, adj[direction]);
      // @ts-ignore
      agent.location = adj[direction];
    }
    const agentCell = this.getAgentCell(agentId);
    if(agentCell.includes('P')) {
      agent.score -= 1e4;
    }
    if(agentCell.includes('W')) {
      agent.score -= 1e5;
    }
    return undefined;
  }

  _pick(agentId, what) {
    const agent = this.getAgent(agentId);
    const agentCell = this.getAgentCell(agentId);
    agent.score -= 1;
    if(agentCell.includes(what)) {
      if(what === 'G') {
        this._gridUnplace('G', ...agent.location);
        agent.score += 1e4
      }
    }
    return undefined;
  }

  /**
   * @param {number} agentId
   * @param {Direction} direction
   */
  _shoot(agentId, direction) {
    const agent = this.getAgent(agentId);
    const agentCell = this.getAgentCell(agentId);
    agent.score -= 1;
    if(agent.arrows > 0) {
      agent.arrows -= 1;
      const location = adjacent(...agent.location, this.n)[direction];
      if(location) {
        const cell = this.getCell(...location)
        if(cell.has('W')) {
          agent.score += 1e4
          this._gridUnplace('W', ...location)
          return ['S']
        }
      }
    }
    return undefined;
  }

  _gridPlace(symbol, x, y) {
    const cell = this.getCell(x, y);
    cell.add(symbol);
  }

  _gridUnplace(symbol, x, y) {
    const cell = this.getCell(x, y);
    cell.delete(symbol);
  }

  _gridReplace(symbol, a, b) {
    this._gridUnplace(symbol, ...a);
    this._gridPlace(symbol, ...b);
  }

  /**
   *
   * @param {number} x
   * @param {number} y
   * @returns {Set<string>} cell.
   */
  getCell(x, y) {
    const cell = this.grid[cellIndex(x, y, this.n)];
    if(!cell) throw new Error(`No cell for [${x}, ${y}]`);
    return cell;
  }

  /**
   * @param {[number, number]} location
   */
  addAgent(location=[0, 0], data={}) {
    if(this.agents.length >= 10) throw new Error('Too many agents');
    const id = this.agents.length;
    const agent = { ...data, location, id, tag: `H${id}`, ...AgentDefaults };
    this.agents.push(agent);
    this._gridPlace(agent.tag, ...agent.location);
    return this.getAgentPercept(id);
  }

  removeAgent(agentId) {
    const agent = this.getAgent(agentId);
    this.agents.splice(agentId, 1);
    this._gridUnplace(agent.tag, ...agent.location);
  }

  /**
   * @param {number} agentId
   * @param {object} update
   */
  setOnAgent(agentId, update) {
    const agent = this.getAgent(agentId);
    this.agents[agentId] = { ...agent, ...pickBy(update, (v, k) => !BaseAgent.includes(k)) };
    return this.agents[agentId]
  }

  getAgent(agentId) {
    const agent = this.agents[agentId];
    if(!agent) throw new Error(`No such agent [${agentId}]`);
    return agent;
  }

  /**
   * @param {number} agentId
   * @returns {string[]}
   */
  getAgentNeighbourPercept(agentId) {
    const percepts = [];
    const agent = this.getAgent(agentId);
    const adj = adjacent(...agent.location, this.n);
    const near = Object.values(adj).filter(v => v).map(v => Array.from(this.getCell(...v))).flat();
    if(near.find((v) => v === 'P')) percepts.push('B'); // Breeze.
    if(near.find((v) => v === 'W')) percepts.push('S'); // Stentch.
    if(near.find((v) => /H.?/.test(v))) percepts.push('R'); // Rival.
    return percepts;
  }

  /**
   *
   * @param {number} agentId
   * @returns {string[]}
   */
  getAgentCell(agentId) {
    const agent = this.getAgent(agentId);
    return Array.from(this.getCell(...agent.location));
  }

  /**
   *
   * @param {number} agentId
   * @param {string[]} morePercepts
   * @returns {{ percept: string[], cell: string[], agent: Agent }}
   */
  getAgentPercept(agentId, morePercepts = []) {
    return {
      percept: [ ...(this.getAgentNeighbourPercept(agentId)), ...morePercepts ],
      cell: this.getAgentCell(agentId),
      agent: this.getAgent(agentId),
    };
  }

  toString() {
    let str = '';
    for(let y = 0; y < this.n; y++) {
      for(let x = 0; x < this.n; x++) {
        str += '[' + Array.from(this.getCell(x, y)).join('').padEnd(5) + ']';
      }
      str += '\n';
    }
    return str.trimEnd();
  }

  /**
   * Dump everything needed to render the game including agent and their scores.
   * @returns
   */
  toSerial() {
    const agents = this.agents.map(v => v);
    const grid = Object.fromEntries(this.grid
      .map((c, i) => ({ i, objects: Array.from(c.values()) }))
      .filter(c => c.objects.length)
      .map(({ i, objects }) => [i, objects])
    );
    return {
      n: this.n,
      agents,
      grid,
    }
  }

  meta() {
    return {
      n: this.n,
      pp: this.pp,
      pg: this.pg,
      numPlayers: this.agents.length,
    };
  }
}