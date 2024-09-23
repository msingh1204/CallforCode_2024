import React from 'react';
import { Button, TextField } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { makeStyles } from '@mui/styles'; // Ensure @mui/styles is installed

// Define styles using makeStyles
const useStyles = makeStyles((theme) => ({
	wrapForm: {
		display: 'flex',
		justifyContent: 'center',
		width: '95%',
		margin: `${theme.spacing(0)} auto`,
	},
	wrapText: {
		width: '100%',
	},
	button: {
		// Uncomment and adjust as needed
		// margin: theme.spacing(1),
	},
}));

export const TextInput = ({ onTextChange, value, inputHandler }) => {
	const classes = useStyles();

	return (
		<form className={classes.wrapForm} noValidate autoComplete='off'>
			<TextField
				value={value}
				onChange={onTextChange}
				id='standard-text'
				label='Please enter your question'
				className={classes.wrapText}
			/>
			<Button
				onClick={inputHandler}
				variant='contained'
				color='primary'
				className={classes.button}>
				<SendIcon />
			</Button>
		</form>
	);
};
