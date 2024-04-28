import { Component, onMount, createSignal, Show, Switch, Match, For } from 'solid-js';
import { createStore } from 'solid-js/store';
import { cellIndex, range } from './utils';

type ScreenState = {
  state: 'LOADING' | 'READY' | 'ERROR',
  error?: Error,
}

let viewerEvents: EventSource;
const baseUrl = '';
const colorWheel = ['red', 'crimson', 'darkorange', 'cyan', 'aqua', 'blue', 'fuchsia', 'deeppink', 'magenta', 'purple'];
const [gameState, setGameState] = createStore({
  n: 0,
  grid: {},
  agents: [],
  state: 'UNKNOWN',
  runTurns: 0,
  turnTime: 0,
  currentTurn: 0,
});
const [screenState, setScreenState] = createSignal<ScreenState>({ state: 'LOADING' });
const [showSettingsDialog, setShowSettingsDialog] = createSignal<boolean>(false);


const Legend = () => {
  return (
    <>
      Agent: <span style={{'font-weight':'bold', 'color': 'red'}}>H</span>&nbsp;
      Pit: <span style={{'font-weight':'bold'}}>P</span>&nbsp;
      Gold: <span style={{'color':'gold','font-weight':'bold'}}>G</span>&nbsp;
      Wumpus: <span style={{'color':'green','font-weight':'bold'}}>W</span>&nbsp;
    </>
  );
};

const Grid = (props) => {
  const GridObject = (s) => {
    const n = () => Number(s.slice(1));
    return <Switch fallback={<span>{s}</span>}>
      <Match when={s === 'P'}>
        <span style={{'font-weight':'bold'}}>P</span>
      </Match>
      <Match when={s === 'G'}>
        <span style={{'color':'gold','font-weight':'bold'}}>G</span>
      </Match>
      <Match when={s === 'W'}>
        <span style={{'color':'green','font-weight':'bold'}}>W</span>
      </Match>
      <Match when={s[0] === 'H'}>
        <span style={{ color: props.game.agents[n()].gone ? 'gray' : colorWheel[n()], 'font-weight': 'bold' }}>H</span>
      </Match>
    </Switch>;
  };
  const gridClass = () => ({
    grid: true,
    'gap-1': true,
    [`grid grid-cols-${props.game.n}`]: true,
  });
  return <div classList={gridClass()}>
    <For each={range(props.game.n)}>
      {(y) => (
          <For each={range(props.game.n)}>
            {(x) => (
              <div class='h-14 w-14 border border-solid border-black' style={{'line-height':'1em','overflow-wrap':'anywhere','font-size':'smaller'}}>
                <For each={props.game.grid[cellIndex(x, y, props.game.n)] || []}>
                  {(k) => GridObject(k)}
                </For>
              </div>
            )}
          </For>
      )}
    </For>
  </div>;
};

const MyButton = (props) => {
  const buttonClass = (disabled = false) => {
    return {
      'opacity-50': disabled,
      'cursor-not-allowed': disabled,
      ... Object.fromEntries('bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 m-2 rounded inline-flex items-center'.split(' ').map(v => [v, true])),
    };
  };
  return <button classList={buttonClass(props.disabled)} onClick={() => props.onClick()}>{props.children}</button>;
};

const SettingsForm = () => {
  let turnTimeRef, runTurnsRef;
  let timer = 0;
  const onChange = () => {
    if (timer) clearTimeout(timer);
    const update = { turnTime: Number(turnTimeRef.value), runTurns: Number(runTurnsRef.value) };
    setTimeout(() => updateSettings(update), 1000);
  };

  return <form onChange={onChange} method="dialog"
    class="m-auto w-1/2 mh-1/4 flex flex-col"
    style={{'border':'solid 1px black','background':'rgba(255, 255, 255,1)'}}
  >
    <div class='m-4 flex flex-row justify-between'>
      <label>Time per Turn (ms):&nbsp;</label>
      <input ref={turnTimeRef} class='border border-black border-solid' type='number' value={gameState.turnTime} />
    </div>
    <div class='m-4 flex flex-row justify-between'>
      <label>Turns per Run:&nbsp;</label>
      <input ref={runTurnsRef} class='border border-black border-solid' type='number' value={gameState.runTurns} />
    </div>
    <div class='flex-1 flex-fill'>&nbsp;</div>
    <div class='flex flex-row justify-end'>
      <MyButton onClick={() => setShowSettingsDialog(false)}><span>CLOSE</span></MyButton>
    </div>
  </form>;
};

const App: Component = () => {
  onMount(() => setTimeout(init, 400));
  return (
    <div class='my-container mx-auto border-box flex flex-col flex-nowrap h-full'>
      <div class='game-controls flex flex-row content-center justify-center w-fill' style={{'align-content':'center'}}>
        <MyButton disabled={!ready()} onClick={(run)}>RUN</MyButton>
        <MyButton disabled={!ready()} onClick={step}>STEP</MyButton>
        <MyButton disabled={!ready()} onClick={stop}>STOP</MyButton>
        <MyButton disabled={!ready()} onClick={restart}>RESTART</MyButton>
        <MyButton disabled={!ready()} onClick={refresh}>
          <span>REFRESH</span>
          <svg class="fill-current w-5 h-5 ml-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><title>refresh</title><path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z" /></svg>
        </MyButton>
        <MyButton disabled={!ready()} onClick={() => setShowSettingsDialog(true)}>
          <svg class="fill-current w-5 h-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><title>settings</title><path d="M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8M12,10A2,2 0 0,0 10,12A2,2 0 0,0 12,14A2,2 0 0,0 14,12A2,2 0 0,0 12,10M10,22C9.75,22 9.54,21.82 9.5,21.58L9.13,18.93C8.5,18.68 7.96,18.34 7.44,17.94L4.95,18.95C4.73,19.03 4.46,18.95 4.34,18.73L2.34,15.27C2.21,15.05 2.27,14.78 2.46,14.63L4.57,12.97L4.5,12L4.57,11L2.46,9.37C2.27,9.22 2.21,8.95 2.34,8.73L4.34,5.27C4.46,5.05 4.73,4.96 4.95,5.05L7.44,6.05C7.96,5.66 8.5,5.32 9.13,5.07L9.5,2.42C9.54,2.18 9.75,2 10,2H14C14.25,2 14.46,2.18 14.5,2.42L14.87,5.07C15.5,5.32 16.04,5.66 16.56,6.05L19.05,5.05C19.27,4.96 19.54,5.05 19.66,5.27L21.66,8.73C21.79,8.95 21.73,9.22 21.54,9.37L19.43,11L19.5,12L19.43,13L21.54,14.63C21.73,14.78 21.79,15.05 21.66,15.27L19.66,18.73C19.54,18.95 19.27,19.04 19.05,18.95L16.56,17.95C16.04,18.34 15.5,18.68 14.87,18.93L14.5,21.58C14.46,21.82 14.25,22 14,22H10M11.25,4L10.88,6.61C9.68,6.86 8.62,7.5 7.85,8.39L5.44,7.35L4.69,8.65L6.8,10.2C6.4,11.37 6.4,12.64 6.8,13.8L4.68,15.36L5.43,16.66L7.86,15.62C8.63,16.5 9.68,17.14 10.87,17.38L11.24,20H12.76L13.13,17.39C14.32,17.14 15.37,16.5 16.14,15.62L18.57,16.66L19.32,15.36L17.2,13.81C17.6,12.64 17.6,11.37 17.2,10.2L19.31,8.65L18.56,7.35L16.15,8.39C15.38,7.5 14.32,6.86 13.12,6.62L12.75,4H11.25Z" />
          </svg>
        </MyButton>
      </div>
      <Show when={showSettingsDialog()}>
        <dialog class="w-full h-full flex flex-col" style={{'background':'rgba(0,0,0,0.5)'}}>
          <SettingsForm />
        </dialog>
      </Show>
      <div class='game-state p-1'>
        <span>GAME_STATE: {gameState.state}</span>;&nbsp;
        <span>TURN: {gameState.currentTurn}/{gameState.runTurns}</span>;&nbsp;
        <span>PLAYERS: {gameState.agents.length}</span>;&nbsp;
        <span>LEGEND: <Legend /></span>
      </div>
      <div class='game-board h-fit flex-100 flex-grow py-1'>
        <div class='flex items-center justify-center h-full'>
          <Switch fallback='Loading ...'>
            <Match when={ready() && gameState.n}>
              <Grid game={{...gameState}} />
            </Match>
            <Match when={screenState().state === 'ERROR'}>
              <em>An error happened</em>
              <MyButton onClick={refresh}>
                <svg class="fill-current w-5 h-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><title>refresh</title><path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z" /></svg>
              </MyButton>
            </Match>
          </Switch>
        </div>
      </div>
      <Switch fallback='Loading ...'>
        <Match when={gameState.agents?.length}>
          <div class='game-score-board grid grid-cols-2 gap-1 my-1 py-1 h-16 flex-grow overflow-y-scroll'>
            <For each={gameState.agents}>{
              (agent) => <div class='mx-1 px-1' style={{'background-color': agent.gone ? 'gray' : colorWheel[agent.id], 'font-family': 'monospace' }}>{JSON.stringify(agent)}</div>
            }</For>
          </div>
        </Match>
        <Match when={!gameState.agents?.length}>
          <div class='game-board h-fit flex-100 flex-grow py-1'>
            <div class='flex items-center justify-center h-full'>
              Waiting for agents to join via API ...
            </div>
          </div>
        </Match>
      </Switch>
      <div class='game-console-log h-12 flex-grow overflow-y-scroll' />
    </div>
  );
};

function ready() {
  return screenState().state === 'READY';
}

function log(m: string, type: 'error' | 'warn' | 'info' | 'debug' = 'info', ...rest) {
    const eventList = document.querySelector('.game-console-log');
    const newElement = document.createElement('p');
    newElement.textContent = `[${type}] ${m}` + (rest.length ? ` [${JSON.stringify(rest)}]` : '');
    eventList?.appendChild(newElement);
    newElement.scrollIntoView();
}

function _setScreenState(state: ScreenState['state'], error?: Error) {
  if (state !== screenState().state) {
    if (state === 'ERROR') {
      log(error?.message, 'error', error);
    }
    log(`${screenState().state} => ${state}`);
  }
  setScreenState({ state, error });
}

/**
 * Initialize state and SSE connection. Also used to re-init in case of NW error.
 * Re EventSource: These thing just annoying stick around after open and auto-
 * reconnect. Don't have much control. Best to just not do anything if already initd.
 */
async function init() {
  _setScreenState('LOADING');
  if (!viewerEvents) {
    viewerEvents = new EventSource(baseUrl + '/viewer/events');
    viewerEvents.onopen = function() {
      log('Connection to server events opened');
    };
    viewerEvents.onmessage = newMessage;
    viewerEvents.onerror = function(e) {
      log('EventSource failed', 'error', e);
    };
  }

  try {
    log('Fetching world ...');
    const response = await fetch(baseUrl + '/world');
    const grid = await response.json();
    setGameState(grid);
    _setScreenState('READY');
  } catch (error) {
    _setScreenState('ERROR', error);
  }
}

function newMessage(e) {
  const { type, payload } = JSON.parse(e.data);
  log('New event', 'info', type);
  console.log(type, payload);
  switch (type) {
    case 'new-game': {
      setGameState(payload);
      break;
    }
    case 'new-agent': {
      setGameState(payload);
      break;
    }
    case 'agent-removed': {
      setGameState(payload);
      break;
    }
    case 'game-running': {
      setGameState(payload);
      break;
    }
    case 'turn-start': {
      setGameState({ ...gameState, currentTurn: payload.i });
      break;
    }
    case 'turn-end': {
      setGameState({ ...payload, currentTurn: payload.i });
      break;
    }
    case 'game-stopped': {
      setGameState(() => ({ ...payload, currentTurn: 0 }));
      break;
    }
    default: {
      log(`Unknown event type "${type}"`, 'error');
    }
  }
}

async function run() {
  console.log('run');
  try {
    const res = await fetch(baseUrl + '/world/run', { method: 'POST' });
    if (!res.ok) {
      const e = await res.json();
      log(e.message, 'error');
    }
  } catch (e) {
    log(e.message, 'error', e);
  }
}

async function step() {
  try {
    const res = await fetch(baseUrl + '/world/step', { method: 'POST' });
    if (!res.ok) {
      const e = await res.json();
      log(e.message, 'error');
    }
  } catch (e) {
    log(e.message, 'error', e);
  }
}

async function stop() {
  try {
    const res = await fetch(baseUrl + '/world/stop', { method: 'POST' });
    if (!res.ok) {
      const e = await res.json();
      log(e.message, 'error', e);
    }
  } catch (e) {
    log(e.message, 'error', e);
  }
}

async function restart() {
  try {
    await fetch(baseUrl + '/world/reset', { method: 'POST' });
  } catch (e) {
    log(e.message, 'error', e);
  }
}

async function updateSettings(settings) {
  try {
    await fetch(baseUrl + '/world/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
      headers: { 'Content-Type': 'application/json' },
    });
    setGameState({ ...gameState, ...settings });
  } catch (e) {
    log(e.message, 'error', e);
  }
}

async function refresh() {
  setTimeout(init, 400);
}

export default App;
