/// Read one byte. The caller must provide a valid aligned pointer.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn fixture_read(ptr: *const u8) -> u8 {
    // SAFETY: caller contract requires a valid pointer to one initialized byte.
    unsafe { *ptr }
}
