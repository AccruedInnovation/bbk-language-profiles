/* Synthetic native-extension signal; not built by the fixture. */
#include <Python.h>

static struct PyModuleDef module = {PyModuleDef_HEAD_INIT, "fixture_native", NULL, -1, NULL};
PyMODINIT_FUNC PyInit_fixture_native(void) { return PyModule_Create(&module); }
