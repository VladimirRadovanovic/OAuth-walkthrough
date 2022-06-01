
import React from 'react';
import { useSelector } from 'react-redux';
import { NavLink } from 'react-router-dom';
import LogoutButton from './auth/LogoutButton';



const NavBar = () => {

  const user = useSelector(state => state.session.user)

  const authenticated = (
    <>
      <li>
        <LogoutButton />
      </li>
    </>
  )

  const notAuthenticated = (
    <>
      <li>
        <NavLink to='/login' exact={true} activeClassName='active'>
          Login
        </NavLink>
      </li>
      <li>
        <NavLink to='/sign-up' exact={true} activeClassName='active'>
          Sign Up
        </NavLink>
      </li>
    </>
  )

  return (
    <nav>
      <ul>
        <li>
          <NavLink to='/' exact={true} activeClassName='active'>
            Home
          </NavLink>
        </li>
        <li>
          <NavLink to='/users' exact={true} activeClassName='active'>
            Users
          </NavLink>
        </li>
        {user ? authenticated : notAuthenticated}
      </ul>
    </nav>
  );
}

export default NavBar;
