import { run } from "../src/worker.js";
void run(new AbortController().signal);
