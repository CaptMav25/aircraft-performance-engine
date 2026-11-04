! Standalone Fortran 2008 demonstration of the C172 accelerating ground roll.
! Build: gfortran -std=f2008 -Wall -Wextra -fcheck=all ground_roll_demo.f90 -o ground_roll_demo
! On macOS, add this option after gfortran if the linker cannot find System:
!   -isysroot "$(xcrun --show-sdk-path)"
! Run: ./ground_roll_demo [time_step_s]     Default step: 0.02 s.
! Compare 0.02 and 0.01 s to check convergence.
! Theory: Mair & Birdsall, Aircraft Performance (1992), Ch. 6.
! Aircraft constants, force models and VR = 1.1 VS1 follow V6.
! RK4 replaces SciPy RK45 here; numerical results are not bit-for-bit identical.
! This is ground roll to VR only: no rotation, airborne segment or BFL.
program ground_roll_demo
    use iso_fortran_env, only: real64
    use, intrinsic :: ieee_arithmetic, only: ieee_is_finite
    implicit none
    real(real64), parameter :: TEMP_SL_K = 288.15_real64
    real(real64), parameter :: PRESS_SL_PA = 101325.0_real64
    real(real64), parameter :: RHO_SL_KG_M3 = 1.225_real64
    real(real64), parameter :: LAPSE_RATE_K_PER_M = 0.0065_real64
    real(real64), parameter :: R_AIR = 287.05_real64
    real(real64), parameter :: G0_MPS2 = 9.80665_real64
    real(real64), parameter :: ALT_MAX_M = 11000.0_real64

    type :: Aircraft
        real(real64) :: s_ref_m2 = 16.2_real64
        real(real64) :: cd0 = 0.032_real64, k_induced = 0.045_real64
        real(real64) :: cl_gnd = 0.4_real64, cl_max_to = 1.5_real64
        real(real64) :: mu_roll = 0.04_real64
        real(real64) :: sls_thrust_n = 2800.0_real64
        real(real64) :: max_power_w = 134000.0_real64, eta_prop = 0.65_real64
    end type Aircraft

    type :: Conditions
        real(real64) :: mass_kg, weight_n, rho_kg_m3, hw_mps, slope_rad
    end type Conditions

    type(Aircraft) :: C172
    real(real64) :: dt_s
    integer :: ios
    character(len=80) :: argument

    dt_s = 0.02_real64
    if (command_argument_count() > 1) error stop 'Usage: ground_roll_demo [time_step_s]'
    if (command_argument_count() == 1) then
        call get_command_argument(1, argument)
        read(argument, *, iostat=ios) dt_s
        if (ios /= 0) error stop 'Invalid time step.'
    end if
    if (.not. ieee_is_finite(dt_s)) error stop 'Time step must be finite.'
    if (dt_s < 0.001_real64 .or. dt_s > 0.5_real64) &
        error stop 'Choose a time step between 0.001 and 0.5 s.'

    print '(a)', 'C172S at 2550 lb: dry paved runway, all engines operating'
    print '(a,f8.4)', 'RK4 time step [s]: ', dt_s
    call run_case('Sea level, ISA, calm, level', 0.0_real64, 0.0_real64, 0.0_real64, 0.0_real64)
    call run_case('5000 ft, ISA+20, calm, level', 1524.0_real64, 20.0_real64, 0.0_real64, 0.0_real64)
    call run_case('Sea level, ISA, 10 kt headwind, 1% uphill', &
        0.0_real64, 0.0_real64, 10.0_real64, 1.0_real64)

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

    subroutine run_case(label, elev_m, isa_dev_c, hw_kt, slope_pct)
        character(len=*), intent(in) :: label
        real(real64), intent(in) :: elev_m, isa_dev_c, hw_kt, slope_pct
        type(Conditions) :: cond
        real(real64) :: temp_k, press_pa, vs1_mps, tas_target_mps, dist_end_m, time_s

        cond%mass_kg = 2550.0_real64 * 0.45359237_real64
        cond%weight_n = cond%mass_kg * G0_MPS2
        call isa(elev_m, isa_dev_c, temp_k, press_pa, cond%rho_kg_m3)
        cond%hw_mps = hw_kt * 1852.0_real64 / 3600.0_real64
        cond%slope_rad = atan(slope_pct / 100.0_real64)
        vs1_mps = stall_speed(C172, cond%weight_n, cond%rho_kg_m3, C172%cl_max_to)
        tas_target_mps = 1.1_real64 * vs1_mps
        call accelerate(C172, cond, tas_target_mps, dist_end_m, time_s)
        print '(/,a)', trim(label)
        print '(a,f14.6)', 'Density [kg/m^3]: ', cond%rho_kg_m3
        print '(a,f14.6)', 'VS1 TAS [m/s]:    ', vs1_mps
        print '(a,f14.6)', 'VR TAS [m/s]:     ', tas_target_mps
        print '(a,f14.6)', 'Ground roll [m]:  ', dist_end_m
        print '(a,f14.6)', 'Time to VR [s]:   ', time_s
    end subroutine run_case

    function stall_speed(acft, weight_n, rho_kg_m3, cl_max) result(vs1_mps)
        type(Aircraft), intent(in) :: acft
        real(real64), intent(in) :: weight_n, rho_kg_m3, cl_max
        real(real64) :: vs1_mps
        vs1_mps = sqrt(2.0_real64 * weight_n / (rho_kg_m3 * acft%s_ref_m2 * cl_max))
    end function stall_speed

    function equations_of_motion(acft, cond, y) result(dy)
        type(Aircraft), intent(in) :: acft
        type(Conditions), intent(in) :: cond
        real(real64), intent(in) :: y(2)
        real(real64) :: dy(2), gs_mps, tas_mps, q_pa, lift_n, drag_n, thrust_n
        real(real64) :: sig, power_avail_w, thrust_cap_n, thrust_prop_n, friction_n, accel_mps2

        gs_mps = y(2)
        tas_mps = gs_mps + cond%hw_mps
        q_pa = 0.5_real64 * cond%rho_kg_m3 * tas_mps**2
        lift_n = q_pa * acft%s_ref_m2 * acft%cl_gnd
        drag_n = q_pa * acft%s_ref_m2 * (acft%cd0 + acft%k_induced * acft%cl_gnd**2)
        sig = cond%rho_kg_m3 / RHO_SL_KG_M3
        power_avail_w = acft%max_power_w * sig
        thrust_cap_n = acft%sls_thrust_n * sig
        thrust_prop_n = acft%eta_prop * power_avail_w / max(tas_mps, 1.0_real64)
        thrust_n = min(thrust_cap_n, thrust_prop_n)
        friction_n = acft%mu_roll * max(cond%weight_n - lift_n, 0.0_real64)
        accel_mps2 = (thrust_n - drag_n - friction_n - &
            cond%weight_n * sin(cond%slope_rad)) / cond%mass_kg
        if (gs_mps <= 0.0_real64) accel_mps2 = max(accel_mps2, 0.0_real64)
        dy = [gs_mps, accel_mps2]
    end function equations_of_motion

    function rk4_step(acft, cond, y, step_s) result(y_next)
        type(Aircraft), intent(in) :: acft
        type(Conditions), intent(in) :: cond
        real(real64), intent(in) :: y(2), step_s
        real(real64) :: y_next(2), k1(2), k2(2), k3(2), k4(2)
        k1 = equations_of_motion(acft, cond, y)
        k2 = equations_of_motion(acft, cond, y + 0.5_real64 * step_s * k1)
        k3 = equations_of_motion(acft, cond, y + 0.5_real64 * step_s * k2)
        k4 = equations_of_motion(acft, cond, y + step_s * k3)
        y_next = y + step_s * (k1 + 2.0_real64*k2 + 2.0_real64*k3 + k4) / 6.0_real64
    end function rk4_step

    subroutine accelerate(acft, cond, tas_target_mps, dist_end_m, time_s)
        type(Aircraft), intent(in) :: acft
        type(Conditions), intent(in) :: cond
        real(real64), intent(in) :: tas_target_mps
        real(real64), intent(out) :: dist_end_m, time_s
        real(real64) :: y(2), y_next(2), step_s, low_s, high_s
        integer :: i

        y = 0.0_real64
        time_s = 0.0_real64
        dist_end_m = 0.0_real64
        if (cond%hw_mps >= tas_target_mps) return
        do while (time_s < 300.0_real64)
            step_s = min(dt_s, 300.0_real64 - time_s)
            y_next = rk4_step(acft, cond, y, step_s)
            if (y_next(2) + cond%hw_mps >= tas_target_mps) then
                ! Shorten the last step so the reported distance ends at VR.
                low_s = 0.0_real64
                high_s = step_s
                do i = 1, 40
                    step_s = 0.5_real64 * (low_s + high_s)
                    y_next = rk4_step(acft, cond, y, step_s)
                    if (y_next(2) + cond%hw_mps < tas_target_mps) then
                        low_s = step_s
                    else
                        high_s = step_s
                    end if
                end do
                dist_end_m = y_next(1)
                time_s = time_s + step_s
                return
            end if
            y = y_next
            time_s = time_s + step_s
        end do
        error stop 'Target TAS was not reached within 300 s.'
    end subroutine accelerate
end program ground_roll_demo
