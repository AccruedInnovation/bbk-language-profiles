//go:build cgo && bbk_native

package native

/*
#include <stdint.h>
*/
import "C"
import "unsafe"

// PointerValue is a fixture-only unsafe boundary.
func PointerValue(pointer unsafe.Pointer) uintptr { return uintptr(pointer) }
