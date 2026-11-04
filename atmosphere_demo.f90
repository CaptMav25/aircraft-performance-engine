! Standalone Fortran 2008 demonstration of V6/atmosphere.py.
! Build: gfortran -std=f2008 -Wall -Wextra -fcheck=all atmosphere_demo.f90 -o atmosphere_demo
! On macOS, add this option after gfortran if the linker cannot find System:
!   -isysroot "$(xcrun --show-sdk-path)"
! Run defaults: ./atmosphere_demo
! Run a case:   ./atmosphere_demo 5000 20
! Arguments: pressure altitude [ft], ISA deviation [deg C].
! Theory: Anderson, Introduction to Flight, 8th ed. (2016).
! Constants and temperature-deviation treatment follow V6.
program atmosphere_demo
    use iso_fortran_env, only: real64
    use, intrinsic :: ieee_arithmetic, only: ieee_is_finite
    implicit none
    real(real64), parameter :: TEMP_SL_K = 288.15_real64
    real(real64), parameter :: PRESS_SL_PA = 101325.0_real64
    real(real64), parameter :: RHO_SL_KG_M3 = 1.225_real64
    real(real64), parameter :: LAPSE_RATE_K_PER_M = 0.0065_real64
    real(real64), parameter :: R_AIR = 287.05_real64
    real(real64), parameter :: G0_MPS2 = 9.80665_real64
    real(real64), parameter :: GAMMA_AIR = 1.4_real64
    real(real64), parameter :: ALT_MAX_M = 11000.0_real64

    real(real64) :: alt_m, isa_dev_c, temp_k, press_pa, rho_kg_m3, alt_ft
    integer :: ios
    character(len=80) :: argument

    alt_ft = 5000.0_real64
    isa_dev_c = 20.0_real64
    if (command_argument_count() /= 0 .and. command_argument_count() /= 2) &
        error stop 'Usage: atmosphere_demo [altitude_ft ISA_deviation_C]'
    if (command_argument_count() == 2) then
        call get_command_argument(1, argument)
        read(argument, *, iostat=ios) alt_ft
        if (ios /= 0) error stop 'Invalid altitude.'
        call get_command_argument(2, argument)
        read(argument, *, iostat=ios) isa_dev_c
        if (ios /= 0) error stop 'Invalid ISA deviation.'
    end if

    alt_m = alt_ft * 0.3048_real64
    call isa(alt_m, isa_dev_c, temp_k, press_pa, rho_kg_m3)
    print '(a)', 'ISA troposphere: V6 atmosphere model'
    print '(a,f14.6)', 'Pressure altitude [ft]: ', alt_ft
    print '(a,f14.6)', 'Pressure altitude [m]:  ', alt_m
    print '(a,f14.6)', 'ISA deviation [deg C]:  ', isa_dev_c
    print '(a,f14.6)', 'Temperature [K]:        ', temp_k
    print '(a,f14.6)', 'Pressure [Pa]:          ', press_pa
    print '(a,f14.6)', 'Density [kg/m^3]:       ', rho_kg_m3
    print '(a,f14.6)', 'Density ratio [-]:     ', sigma(alt_m, isa_dev_c)
    print '(a,f14.6)', 'Speed of sound [m/s]:   ', speed_of_sound(alt_m, isa_dev_c)

contains
    subroutine isa(alt_m, isa_dev_c, temp_k, press_pa, rho_kg_m3)
        real(real64), intent(in) :: alt_m, isa_dev_c
        real(real64), intent(out) :: temp_k, press_pa, rho_kg_m3
        real(real64) :: temp_std_k

        if (.not. ieee_is_finite(alt_m) .or. .not. ieee_is_finite(isa_dev_c)) &
            error stop 'Atmosphere inputs must be finite.'
        if (alt_m < 0.0_real64 .or. alt_m > ALT_MAX_M) &
            error stop 'Pressure altitude must be between 0 and 11000 m.'
        temp_std_k = TEMP_SL_K - LAPSE_RATE_K_PER_M * alt_m
        temp_k = temp_std_k + isa_dev_c
        if (temp_k <= 0.0_real64) error stop 'Temperature must be above 0 K.'
        ! Pressure altitude uses the standard profile, even on a hot day.
        press_pa = PRESS_SL_PA * (temp_std_k / TEMP_SL_K) ** &
            (G0_MPS2 / (LAPSE_RATE_K_PER_M * R_AIR))
        rho_kg_m3 = press_pa / (R_AIR * temp_k)
    end subroutine isa

    function sigma(alt_m, isa_dev_c) result(sig)
        real(real64), intent(in) :: alt_m, isa_dev_c
        real(real64) :: sig, temp_k, press_pa, rho_kg_m3
        call isa(alt_m, isa_dev_c, temp_k, press_pa, rho_kg_m3)
        sig = rho_kg_m3 / RHO_SL_KG_M3
    end function sigma

    function speed_of_sound(alt_m, isa_dev_c) result(a)
        real(real64), intent(in) :: alt_m, isa_dev_c
        real(real64) :: a, temp_k, press_pa, rho_kg_m3
        call isa(alt_m, isa_dev_c, temp_k, press_pa, rho_kg_m3)
        a = sqrt(GAMMA_AIR * R_AIR * temp_k)
    end function speed_of_sound
end program atmosphere_demo
