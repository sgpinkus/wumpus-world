import { adjacent, cellIndex, WumpusWorld } from './index.js';
import { expect } from 'chai';

describe('Utils', function() {
  it('adjacent', function() {
    /** @type [[number, number, number], number][] */
    const _tests = [
      [[0,0,8], 3],
      [[0,1,8], 5],
      [[1,1,8], 8],
      [[8,8,8], 1],
      [[9,9,8], 0],
    ];
    for(let x of _tests) {
      const [v, r] = x;
      expect(Object.values(adjacent(...v)).filter(v => v).length).equals(r);
    }
  });

  it('cellIndex', function() {
    expect(cellIndex(0,0,1)).equals(0);
    expect(cellIndex(1,1,2)).equals(3);
  });
});

const w = new WumpusWorld(4, 0.25);
const { agent } = w.addAgent();
for(let direction of ['SE', 'SE', 'SE', 'SE', 'N', 'N', 'N', 'N', 'SW', 'SW', 'SW', 'SW']) {
  console.log(w.toString());
  console.log(w.getAgentPercept(agent.id));
  // @ts-ignore
  w.action(agent.id, 'MOVE', { direction });
  w.action(agent.id, 'PICK', { what: 'G' });
  const _percept = w.action(agent.id, 'SHOOT', { direction });
  if(_percept.percept.includes('S')) console.log('KILL');
  console.log('-'.repeat(50));
}
console.log(w.getAgentPercept(agent.id));
console.log(w.toString());


// console.dir(w.toSerial(), { depth: null });