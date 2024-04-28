/**
 * Wumpus world manager and API.
 */
import path from 'node:path';
import { PassThrough } from 'node:stream';
import Koa from 'koa';
import KoaStatic from 'koa-static';
import KoaRouter from 'koa-router';
import morgan from 'koa-morgan';
import bodyParser from '@koa/bodyparser';
import lodash from 'lodash';
import world from './world-harness.js';
import { LogicError, InvalidInputError } from './errors.js'

const app = new Koa();

// Error and fallthru 404 handler.
app.use(async (ctx, next) => {
  try {
    await next();
    const status = ctx.status || 404
    if (status === 404) {
      ctx.throw(404)
    }
  } catch (err) {
    function fileLine(error, n = 1) { // eslint-disable-line
      try {
        return `${error.message} ${error.stack?.split(/\n\s*/).slice(1, n + 1).join(', ') || '[no-stack]'}`;
      } catch (err) {
        return '-';
      }
    }
    console.info('Hit error handler', { tags: 'server', error: fileLine(err) });
    let [error, message, status] = ['Error', 'Server error', 500];
    status = err.status || 500;
    message = `${err.message}`;
    error = err.name;
    ctx.status = status;
    ctx.body = { error, message, status };
  }
});

app.use(bodyParser());

app.use(morgan('common', { stream: { write: message => { console.info(message.trim(), { tags: 'http' }); } } }));

app.use(KoaStatic(path.join('.', 'public')));

app.use(async (ctx, next) => { // https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
  ctx.set({
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': ['Content-Type']
  });
  await next();
});

const router = new KoaRouter();

router.get('/world/meta', (ctx) => {
  ctx.body = world.meta();
});

router.get('/world', (ctx) => {
  ctx.body = world.toSerial();
});

router.post('/world/settings', (ctx) => {
  const settings = ctx.request.body;
  if(!lodash.isObject(settings)) throw new InvalidInputError();
  // @ts-ignore
  const { runTurns, turnTime } = settings;
  if(runTurns) world.runTurns = Number(runTurns);
  if(turnTime) world.turnTime = Number(turnTime);
  ctx.status = 204;
});

router.post('/world/run', (ctx) => {
  try {
    ctx.body = world.run();
  }
  catch(e) {
    throw new LogicError(e.message);
  }
});

router.post('/world/step', (ctx) => {
  try {
    ctx.body = world.step();
  }
  catch(e) {
    throw new LogicError(e.message);
  }
});

router.post('/world/stop', (ctx) => {
  ctx.body = world.stop();
});

router.post('/world/reset', (ctx) => {
  ctx.body = world.reset();
});

router.post('/agent/join', (ctx) => {
  const agent = world.addAgent();
  ctx.body = agent;
});

router.post('/agent/:agentId/action', (ctx) => {
  // @ts-ignore
  const agentId = ctx.params.agentId;
  const agent = world.getAgent(agentId);
  const { type, payload } = ctx.request.body;
  ctx.body = world.action(agent.id, type, payload);
});

router.get('/agent/:agentId/events', function (ctx) {
  const agentId = ctx.params.agentId;
  const agent = world.getAgent(agentId);
  _setupConnection(ctx);
  const stream = new PassThrough();
  ctx.status = 200;
  ctx.body = stream;

  // Handlers need to be addressable by EventEmitter.removeListener if you want to rm them - which we do.
  const handlers = {
    newGame: (payload) => {
      stream.write(`data: ${JSON.stringify({ type: 'new-game', payload })}\n\n`);
      stream.end();
    },
    turnStart: (payload) => {
      stream.write(`data: ${JSON.stringify({ type: 'turn-start', payload })}\n\n`);
    },
    gameStopped: (payload) => {
      stream.write(`data: ${JSON.stringify({ type: 'game-stopped', payload })}\n\n`);
    }
  }

  stream.write(`data: ${JSON.stringify({ type: 'new-agent', payload: agent })}\n\n`);
  world.events.on('turn-start', handlers.turnStart);
  world.events.on('game-stopped', handlers.gameStopped);
  world.events.on('new-game', handlers.newGame);
  stream.on('close', () => {
    try {
      console.log(`Client agent connection closed [${agent.id}]`);
      world.removeAgent(agent.id);
      setTimeout(() => Object.values(handlers).forEach(h => world.off(h), 0));
    } catch {}
  });
  stream.on('error', () => {
    try {
      console.log(`Client agent connection error [${agent.id}]`);
      world.removeAgent(agent.id);
      setTimeout(() => Object.values(handlers).forEach(h => world.off(h)));
    } catch {}
  });
});

router.get('/viewer/events', function (ctx) {
  _setupConnection(ctx);
  const stream = new PassThrough();
  ctx.status = 200;
  ctx.body = stream;

  const handlers = {
    newGame: () => {
      stream.write(`data: ${JSON.stringify({ type: 'new-game', payload: world.toSerial() })}\n\n`);
    },
    gameRunning: () => {
      stream.write(`data: ${JSON.stringify({ type: 'game-running', payload: world.toSerial() })}\n\n`);
    },
    gameStopped: () => {
      stream.write(`data: ${JSON.stringify({ type: 'game-stopped', payload: world.toSerial() })}\n\n`);
    },
    turnStart: (payload) => {
      stream.write(`data: ${JSON.stringify({ type: 'turn-start', payload })}\n\n`);
    },
    turnEnd: () => {
      stream.write(`data: ${JSON.stringify({ type: 'turn-end', payload: world.toSerial() })}\n\n`);
    },
    newAgent: () => {
      stream.write(`data: ${JSON.stringify({ type: 'new-agent', payload: world.toSerial() })}\n\n`);
    },
    agentRemoved: () => {
      stream.write(`data: ${JSON.stringify({ type: 'agent-removed', payload: world.toSerial() })}\n\n`);
    }
  };

  world.events.on('new-game', handlers.newGame);
  world.events.on('game-running', handlers.gameRunning);
  world.events.on('game-stopped', handlers.gameStopped);
  world.events.on('turn-start', handlers.turnStart);
  world.events.on('turn-end', handlers.turnEnd);
  world.events.on('new-agent', handlers.newAgent);
  world.events.on('agent-removed', handlers.agentRemoved);
  stream.on('close', () => {
    console.log('Client connection closed');
    setTimeout(() => Object.values(handlers).forEach(h => world.off(h)))
  });
  // stream.on('error', () => {
  //   console.log('Client viewer connection error');
  //   Object.values(handlers).forEach(h => world.off(h));
  //   stream.end()
  // });
});

router.get('/events/test', function (ctx) {
  ctx.request.socket.setTimeout(0);
  ctx.req.socket.setNoDelay(true);
  ctx.req.socket.setKeepAlive(true);
  ctx.set({
    'Cache-Control': 'no-cache',
    'Content-Type': 'text/event-stream',
    'Connection': 'keep-alive'
  });
  // ctx.response.flushHeaders(); DONT DO THIS.
  const stream = new PassThrough();
  ctx.status = 200;
  ctx.body = stream;
  const message = () => {
    stream.write(`data: {"time": "${Date.now()}"}\n\n`);
  };
  const timer = setInterval(message, 1000);
  stream.on('close', () => {
    clearInterval(timer);
  });
});

app
  .use(router.routes())
  .use(router.allowedMethods({ throw: true }));


function _setupConnection(ctx) {
  ctx.request.socket.setTimeout(0);
  ctx.req.socket.setNoDelay(true);
  ctx.req.socket.setKeepAlive(true);
  ctx.set({
    'Cache-Control': 'no-cache',
    'Content-Type': 'text/event-stream',
    'Connection': 'keep-alive'
  });
}

export default app;